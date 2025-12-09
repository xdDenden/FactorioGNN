# main.py
import torch
import traceback
import time
import random  # Needed for epsilon-greedy
from config import Config
from environment import FactorioEnv
from FactorioHGNN import FactorioHGNN


# /c game.speed = 4
#test


def main():
    # 1. Setup
    cfg = Config()
    env = FactorioEnv(cfg)

    # 2. Initialize Model
    use_mps = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    device = torch.device("cuda" if torch.cuda.is_available() else ("mps" if use_mps else "cpu"))
    model = FactorioHGNN(
        hidden_dim=cfg.HIDDEN_DIM,
        lstm_hidden_dim=cfg.LSTM_HIDDEN_DIM
    ).to(device)

    model.eval()
    hidden_state = None

    # Point 1: Epsilon-Greedy Setup
    epsilon = 0.2  # Exploration rate (could be moved to Config)

    # 3. Reset Environment
    observation = env.reset()
    if observation is None:
        return

    print(f"Starting Loop for {cfg.MAX_TIMESTEPS} steps...")

    try:
        for step in range(cfg.MAX_TIMESTEPS):
            # A. Get Data
            node_features, H = observation
            node_features = node_features.to(device)
            H = H.to(device)

            # B. Model Inference
            with torch.no_grad():
                (action_logits,
                 item_logits,
                 rotation_logits,
                 heatmap_logits,
                 hidden_state) = model(node_features, H, hidden_state)

            # C. Select Action - Point 1: Epsilon Greedy
            if random.random() < epsilon:
                # Random Exploration
                action_idx = random.randint(0, action_logits.shape[-1] - 1)
                item_idx = random.randint(0, item_logits.shape[-1] - 1)
                rotation_idx = random.randint(0, rotation_logits.shape[-1] - 1)
                # Random heatmap pos
                x_grid_idx = random.randint(0, 16)
                y_grid_idx = random.randint(0, 16)
            else:
                # Greedy Exploitation
                action_idx = torch.argmax(action_logits).item()
                item_idx = torch.argmax(item_logits).item()
                rotation_idx = torch.argmax(rotation_logits).item()

                flat_max_idx = torch.argmax(heatmap_logits)
                y_grid_idx = (flat_max_idx // 17).item()
                x_grid_idx = (flat_max_idx % 17).item()

            # Normalize 0..16 grid to -1.0..1.0
            x_norm = -1.0 + (x_grid_idx / 16.0) * 2.0
            y_norm = -1.0 + (y_grid_idx / 16.0) * 2.0

            # D. Step Environment
            observation, reward, done, info = env.step(action_idx, item_idx, rotation_idx, x_norm, y_norm)

            # Print reward for debugging
            if cfg.VERBOSE or reward != 0:
                print(f"[Step {step}] Reward: {reward:.4f}")

            if done:
                print("Goal Reached!")
                break

    except KeyboardInterrupt:
        print("\nStopping manually...")
    except Exception as e:
        print(f"Error in main loop: {e}")
        traceback.print_exc()
    finally:
        env.close()
        print("Run finished.")


if __name__ == "__main__":
    main()