# train_dqn.py
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque
from tqdm import tqdm
from config import Config
from environment import FactorioEnv
from FactorioHGNN import FactorioHGNN
import timeit

# --- Hyperparameters ---
GAMMA = 0.99
LR = 1e-4
BATCH_SIZE = 32
BUFFER_SIZE = 10000
EPSILON_START = 1.0
EPSILON_END = 0.05
EPSILON_DECAY = 2000
TARGET_UPDATE = 200
NUM_EPISODES = 50


class ReplayBuffer:
    def __init__(self, capacity):
        self.buffer = deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        """
        state: (node_tensor, H_tensor)
        action: (act_idx, item_idx, rot_idx, heatmap_idx)
        """
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        return random.sample(self.buffer, batch_size)

    def __len__(self):
        return len(self.buffer)


def select_action(model, node_feats, H, hidden_state, epsilon, device):
    """Epsilon-Greedy Policy for Branching Output"""
    if random.random() < epsilon:
        # Random Exploration
        act = random.randint(0, 7)  # 8 Actions
        item = random.randint(0, 50)  # Approx Items
        rot = random.randint(0, 3)  # 4 Rotations
        heatmap_idx = random.randint(0, 17 * 17 - 1)  # 289 locations

        # Return dummy hidden state for continuity
        h_next = (torch.zeros(1, 256).to(device), torch.zeros(1, 256).to(device))
        return act, item, rot, heatmap_idx, h_next
    else:
        # Greedy Exploitation
        with torch.no_grad():
            q_act, q_item, q_rot, q_map, h_next = model(node_feats, H, hidden_state)

            act = q_act.argmax().item()
            item = q_item.argmax().item()
            rot = q_rot.argmax().item()
            heatmap_idx = q_map.view(-1).argmax().item()

            return act, item, rot, heatmap_idx, h_next


def train():
    cfg = Config()
    env = FactorioEnv(cfg)

    if torch.backends.mps.is_available():
        device = torch.device("mps")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")
    print(f"Training on {device}")

    # 1. Initialize Networks
    policy_net = FactorioHGNN(hidden_dim=cfg.HIDDEN_DIM, lstm_hidden_dim=cfg.LSTM_HIDDEN_DIM).to(device)
    target_net = FactorioHGNN(hidden_dim=cfg.HIDDEN_DIM, lstm_hidden_dim=cfg.LSTM_HIDDEN_DIM).to(device)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()

    optimizer = optim.Adam(policy_net.parameters(), lr=LR)
    memory = ReplayBuffer(BUFFER_SIZE)
    criterion = nn.MSELoss()

    steps_done = 0

    # === OUTER PROGRESS BAR (Episodes) ===
    outer_bar = tqdm(range(NUM_EPISODES), desc="Total Progress", unit="ep")

    for episode in outer_bar:
        obs = env.reset()
        if obs is None: continue

        # Reset LSTM hidden state (Batch=1)
        hidden_state = (torch.zeros(1, cfg.LSTM_HIDDEN_DIM).to(device),
                        torch.zeros(1, cfg.LSTM_HIDDEN_DIM).to(device))

        total_reward = 0
        step_times = []  # Keep track for average calc

        # === INNER PROGRESS BAR (Steps within Episode) ===
        # leave=False ensures the bar clears when the episode ends
        with tqdm(range(cfg.MAX_TIMESTEPS), desc=f"Ep {episode + 1}", leave=False) as inner_bar:

            for t in inner_bar:
                step_start_time = timeit.default_timer()

                # === CRITICAL FIX: Refresh observation after the first step ===
                if t > 0:
                    obs = env.get_observation()

                node_feats, H = obs
                node_feats = node_feats.to(device)
                H = H.to(device)

                # 1. Action Selection
                epsilon = EPSILON_END + (EPSILON_START - EPSILON_END) * \
                          np.exp(-1. * steps_done / EPSILON_DECAY)

                act, item, rot, map_idx, next_hidden = select_action(
                    policy_net, node_feats, H, hidden_state, epsilon, device
                )

                # Convert Heatmap Index -> Norm Coords
                y_grid = map_idx // 17
                x_grid = map_idx % 17
                x_norm = -1.0 + (x_grid / 16.0) * 2.0
                y_norm = -1.0 + (y_grid / 16.0) * 2.0

                # 2. Environment Step
                next_obs, reward, done, _ = env.step(act, item, rot, x_norm, y_norm)
                total_reward += reward

                # 3. Store Transition
                if next_obs is not None:
                    # Store tensors on CPU to save VRAM
                    action_tuple = (act, item, rot, map_idx)
                    memory.push((node_feats.cpu(), H.cpu()), action_tuple, reward,
                                (next_obs[0].cpu(), next_obs[1].cpu()), done)

                    hidden_state = next_hidden

                # 4. Train Step
                loss_val = 0.0  # Just for display
                if len(memory) > BATCH_SIZE:
                    transitions = memory.sample(BATCH_SIZE)
                    # Unzip batch
                    batch_state, batch_action, batch_reward, batch_next_state, batch_done = zip(*transitions)

                    loss_total = 0

                    # Manual Batch Processing (Variable Graph Sizes)
                    for i in range(BATCH_SIZE):
                        s_nodes, s_H = batch_state[i]
                        a_act, a_item, a_rot, a_map = batch_action[i]
                        r = batch_reward[i]
                        ns_nodes, ns_H = batch_next_state[i]
                        d = batch_done[i]

                        s_nodes, s_H = s_nodes.to(device), s_H.to(device)
                        ns_nodes, ns_H = ns_nodes.to(device), ns_H.to(device)

                        # Reset hidden state for stateless Q-learning update
                        dummy_h = (torch.zeros(1, cfg.LSTM_HIDDEN_DIM).to(device),
                                   torch.zeros(1, cfg.LSTM_HIDDEN_DIM).to(device))

                        # Predicted Q values
                        q_act_v, q_item_v, q_rot_v, q_map_v, _ = policy_net(s_nodes, s_H, dummy_h)

                        # Target Q values
                        with torch.no_grad():
                            if d:
                                target_val = r
                            else:
                                nq_act, nq_item, nq_rot, nq_map, _ = target_net(ns_nodes, ns_H, dummy_h)
                                # Average Max Q across heads
                                max_q = (nq_act.max() + nq_item.max() + nq_rot.max() + nq_map.max()) / 4.0
                                target_val = r + GAMMA * max_q

                        target_tensor = torch.tensor([target_val], device=device)

                        # Loss per head
                        l1 = criterion(q_act_v[0, a_act].unsqueeze(0), target_tensor)
                        l2 = criterion(q_item_v[0, a_item].unsqueeze(0), target_tensor)
                        l3 = criterion(q_rot_v[0, a_rot].unsqueeze(0), target_tensor)
                        l4 = criterion(q_map_v.view(-1)[a_map].unsqueeze(0), target_tensor)

                        loss_total += (l1 + l2 + l3 + l4)

                    optimizer.zero_grad()
                    (loss_total / BATCH_SIZE).backward()
                    optimizer.step()
                    loss_val = (loss_total / BATCH_SIZE).item()

                # 5. Target Update
                steps_done += 1
                if steps_done % TARGET_UPDATE == 0:
                    target_net.load_state_dict(policy_net.state_dict())
                    # Use tqdm.write so it prints above the progress bars cleanly
                    tqdm.write(f"--> Updated Target Net at step {steps_done}")

                step_end_time = timeit.default_timer()
                step_duration = step_end_time - step_start_time
                step_times.append(step_duration)

                # === UPDATE INNER BAR (Real-time feedback) ===
                inner_bar.set_postfix(
                    Rew=f"{total_reward:.1f}",
                    Eps=f"{epsilon:.2f}",
                    StepT=f"{step_duration:.3f}s",
                    Loss=f"{loss_val:.2f}"
                )

                if done:
                    break

        # === UPDATE OUTER BAR (End of episode stats) ===
        avg_ep_time = np.mean(step_times) if step_times else 0
        outer_bar.set_postfix(LastRew=f"{total_reward:.1f}", AvgTime=f"{avg_ep_time:.3f}s")

    torch.save(policy_net.state_dict(), "jimbo_dqn_weights.pth")
    print("\nModel saved to jimbo_dqn_weights.pth")
    env.close()


if __name__ == "__main__":
    train()
