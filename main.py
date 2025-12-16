import torch
import traceback
import random
import numpy as np
from config import Config
from environment import FactorioEnv
from FactorioHGNN import FactorioHGNN
from ActionMasking import get_action_masks

def apply_mask_to_logits(logits, mask):
    mask_t = torch.tensor(mask, device=logits.device, dtype=torch.bool)
    masked_logits = logits.clone()
    masked_logits[~mask_t] = -1e9
    return masked_logits

# /c game.speed = 4
#test


def main():
    # 1. Setup
    cfg = Config()
    env = FactorioEnv(cfg)

    # 2. Initialize Model
    use_mps = hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    device = torch.device("cuda" if torch.cuda.is_available() else ("mps" if use_mps else "cpu"))
    print(f"Running on {device}")
    model = FactorioHGNN(
        hidden_dim=cfg.HIDDEN_DIM,
        lstm_hidden_dim=cfg.LSTM_HIDDEN_DIM
    ).to(device)

   # Load weights if available
    try:
        model.load_state_dict(torch.load("jimbo_dqn_weights.pth", map_location=device))
        print("Loaded weights from jimbo_dqn_weights.pth")
    except FileNotFoundError:
        print("No weights found, running with random init.")

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

            # --- MASK GENERATION ---
            raw_entities = env._last_raw_entities
            raw_player = env._last_raw_player
            inv_list = raw_player.get('inventory', [])
            inventory = {item.get('name'): item.get('count', 0) for item in inv_list}
            bounds = env.current_bounds

            act_mask, item_mask, space_mask = get_action_masks(
                entities=raw_entities,
                player_info=raw_player,
                inventory=inventory,
                science_level=1,
                bounds=bounds,
                move_state=env.move_state
            )

            # B. Model Inference
            with torch.no_grad():
                (action_logits,
                 item_logits,
                 rotation_logits,
                 heatmap_logits,
                 hidden_state) = model(node_features, H, hidden_state)

            # C. Select Action - Point 1: Epsilon Greedy
            if random.random() < epsilon:
                # --- MASKED RANDOM ---
                valid_actions = np.nonzero(act_mask)[0]
                action_idx = random.choice(valid_actions) if len(valid_actions) > 0 else 0

                valid_items = np.nonzero(item_mask[action_idx])[0]
                item_idx = random.choice(valid_items) if len(valid_items) > 0 else 0

                rotation_idx = random.randint(0, 3)

                valid_locs = np.nonzero(space_mask[action_idx])[0]
                flat_map_idx = random.choice(valid_locs) if len(valid_locs) > 0 else 0

                y_grid_idx = flat_map_idx // 17
                x_grid_idx = flat_map_idx % 17

            else:
                # --- MASKED GREEDY ---
                # 1. Action
                masked_act_logits = apply_mask_to_logits(action_logits.view(-1), act_mask)
                action_idx = torch.argmax(masked_act_logits).item()

                # 2. Item
                masked_item_logits = apply_mask_to_logits(item_logits.view(-1), item_mask[action_idx])
                item_idx = torch.argmax(masked_item_logits).item()

                # 3. Rotation
                rotation_idx = torch.argmax(rotation_logits).item()

                # 4. Heatmap
                masked_map_logits = apply_mask_to_logits(heatmap_logits.view(-1), space_mask[action_idx])
                flat_max_idx = torch.argmax(masked_map_logits)
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