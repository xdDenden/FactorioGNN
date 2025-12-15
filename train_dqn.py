import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque, defaultdict
from tqdm import tqdm

from OrePatchDetector import OrePatchDetector
from config import Config
from environment import FactorioEnv
from FactorioHGNN import FactorioHGNN
from plotting import TrainingLogger
from rcon_bridge_1_0_0.rcon_bridge import Rcon_reciever
from ActionMasking import get_action_masks
import timeit

# --- Hyperparameters ---
GAMMA = 0.99  # Discount factor for future rewards
LR = 1e-4  # Learning rate for the optimizer
BATCH_SIZE = 32  # Number of samples per training batch
BUFFER_SIZE = 50000  # Maximum size of the replay buffer
EPSILON_START = 1.0  # Initial value of epsilon for epsilon-greedy policy
EPSILON_END = 0.05  # Minimum value of epsilon for epsilon-greedy policy
EPSILON_DECAY = 25000  # Decay rate for epsilon over time
TARGET_UPDATE = 200  # Frequency of target network updates (in gradient steps)
NUM_EPISODES = 50  # Total number of episodes to train the model


class TimingTracker:
    """Tracks timing statistics for different operations."""
    def __init__(self):
        self.totals = defaultdict(float)
        self.counts = defaultdict(int)
        self.last = {}

    def record(self, name, duration):
        self.totals[name] += duration
        self.counts[name] += 1
        self.last[name] = duration

    def reset(self):
        self.totals = defaultdict(float)
        self.counts = defaultdict(int)
        self.last = {}

    def print_report(self, step_count):
        tqdm.write("\n" + "="*70)
        tqdm.write(f"TIMING REPORT (Last {step_count} steps)")
        tqdm.write("="*70)

        # Sort by total time descending
        sorted_ops = sorted(self.totals.items(), key=lambda x: -x[1])

        for name, total in sorted_ops:
            count = self.counts[name]
            avg_ms = (total / count * 1000) if count > 0 else 0
            tqdm.write(f"  {name:<24}: avg={avg_ms:>8.2f}ms, total={total:>8.2f}s, count={count}")

        total_time = sum(self.totals.values())
        tqdm.write("-"*70)
        tqdm.write(f"  {'TOTAL':<24}: total={total_time:>8.2f}s")
        tqdm.write("="*70 + "\n")


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


def apply_mask_to_logits(logits, mask):
    """
    Sets logits to -inf where mask is 0.
    logits: Tensor
    mask: Numpy array or Tensor (0/1)
    """
    # Create a tensor mask on the same device
    if not isinstance(mask, torch.Tensor):
        mask_t = torch.tensor(mask, device=logits.device, dtype=torch.bool)
    else:
        mask_t = mask.bool()

    # Fill illegal actions with -inf
    # clone to avoid in-place modification errors if needed
    masked_logits = logits.clone()
    masked_logits[~mask_t] = -1e9
    return masked_logits


def select_action(model, node_feats, H, hidden_state, epsilon, device, masks):
    """
    Epsilon-Greedy with Action Masking.
    masks: (action_mask, item_mask, spatial_mask) from ActionMasking.py
    """
    act_mask, item_mask, space_mask = masks

    if random.random() < epsilon:
        # --- MASKED RANDOM EXPLORATION ---

        # 1. Select Action from valid indices
        valid_actions = np.nonzero(act_mask)[0]
        if len(valid_actions) == 0:
            act = 0 # Fallback to No-Op
        else:
            act = random.choice(valid_actions)

        # 2. Select Item from valid indices FOR THAT ACTION
        # item_mask is [num_actions, num_items]
        valid_items = np.nonzero(item_mask[act])[0]
        if len(valid_items) == 0:
            item = 0 # Default/No-Item
        else:
            item = random.choice(valid_items)

        # 3. Select Rotation (Unmasked for now)
        rot = random.randint(0, 3)

        # 4. Select Heatmap Location from valid indices FOR THAT ACTION
        # space_mask is [num_actions, grid_size]
        valid_locs = np.nonzero(space_mask[act])[0]
        if len(valid_locs) == 0:
            heatmap_idx = 0 # Default
        else:
            heatmap_idx = random.choice(valid_locs)

        # Return dummy hidden state
        h_next = (torch.zeros(1, 256).to(device), torch.zeros(1, 256).to(device))
        return act, item, rot, heatmap_idx, h_next

    else:
        # --- MASKED GREEDY EXPLOITATION ---
        with torch.no_grad():
            q_act, q_item, q_rot, q_map, h_next = model(node_feats, H, hidden_state)

            # 1. Mask Action Logits
            masked_q_act = apply_mask_to_logits(q_act.view(-1), act_mask)
            act = masked_q_act.argmax().item()

            # 2. Mask Item Logits (based on chosen action)
            # q_item is [1, num_items], item_mask[act] is [num_items]
            masked_q_item = apply_mask_to_logits(q_item.view(-1), item_mask[act])
            item = masked_q_item.argmax().item()

            # 3. Rotation (Unmasked)
            rot = q_rot.argmax().item()

            # 4. Mask Heatmap (based on chosen action)
            masked_q_map = apply_mask_to_logits(q_map.view(-1), space_mask[act])
            heatmap_idx = masked_q_map.argmax().item()

            return act, item, rot, heatmap_idx, h_next



def train():
    cfg = Config()
    env = FactorioEnv(cfg)
    logger = TrainingLogger()

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


    # Counters
    env_steps_done = 0
    updates_done = 0
    steps_since_train = 0

    # Timing
    timer = TimingTracker()
    steps_since_report = 0

    # === OUTER PROGRESS BAR (Episodes) ===
    outer_bar = tqdm(range(NUM_EPISODES), desc="Total Progress", unit="ep")

    for episode in outer_bar:

        # initalize ore map to know what to mine and where
        # save it to a file for use in ActionMasking
        # only need to do this once per episode because thats when the map resets
        # also time between episodes is long enough to not worry about timing this or it slowing down training
        receiver_ore = Rcon_reciever("localhost", "eenie7Uphohpaim", 27015)
        ore_map = receiver_ore.scan_ore()

        # Save as JSON instead of string representation
        import json
        with open("ore_map.json", "w") as ore_file:
            json.dump(ore_map, ore_file)
        receiver_ore.disconnect()

        # Then process the ores map for use in ActionMasking
        # The ores will be converted from millions of individual nodes into a smaller number of patches
        # this is necessary for performance reasons
        with open("ore_map.json", "r") as f:
            ore_data = json.load(f)  # This loads it as a proper list of dicts

        detector = OrePatchDetector(ore_data)
        patches = detector.process_patches()

        with open("patches.json", "w") as patches_file:
            # Save patches too (without the polygon objects though)
            patches_serializable = [{k: v for k, v in p.items() if k != 'polygon'} for p in patches]
            json.dump(patches_serializable, patches_file)

        #again we will save the patches to a file for use in ActionMasking

        # --- Time: Reset ---
        t_start = timeit.default_timer()
        obs = env.reset()
        timer.record('reset', timeit.default_timer() - t_start)

        if obs is None: continue

        # Reset LSTM hidden state (Batch=1)
        hidden_state = (torch.zeros(1, cfg.LSTM_HIDDEN_DIM).to(device),
                        torch.zeros(1, cfg.LSTM_HIDDEN_DIM).to(device))

        total_reward = 0
        step_times = []

        episode_loss_accum = 0.0
        episode_train_steps = 0
        last_epsilon = EPSILON_START
        # === INNER PROGRESS BAR (Steps within Episode) ===
        with tqdm(range(cfg.MAX_TIMESTEPS), desc=f"Ep {episode + 1}", leave=False) as inner_bar:

            for t in inner_bar:
                step_start_time = timeit.default_timer()

                # --- Time: Observation Fetch ---
                t_start = timeit.default_timer()
                if t > 0:
                    obs = env.get_observation()
                timer.record('obs_fetch', timeit.default_timer() - t_start)

                # --- Time: Preprocessing / To Device ---
                t_start = timeit.default_timer()
                node_feats, H = obs
                node_feats = node_feats.to(device)
                H = H.to(device)
                timer.record('preproc_to_device', timeit.default_timer() - t_start)

                # 3. Calculate MASKS
                t_start = timeit.default_timer()

                # Extract state info from env for masking
                raw_entities = env._last_raw_entities
                raw_player = env._last_raw_player
                # Convert inventory list to dict {name: count}
                inv_list = raw_player.get('inventory', [])
                inventory = {item.get('name'): item.get('count', 0) for item in inv_list}

                bounds = env.current_bounds

                masks = get_action_masks(
                    entities=raw_entities,
                    player_info=raw_player,
                    inventory=inventory,
                    science_level=1, # Placeholder
                    bounds=bounds,
                    patches = patches
                )
                timer.record('mask_calc', timeit.default_timer() - t_start)

                # --- DEBUG PRINT (Check once per 100 steps) ---
                if t % 100 == 0:
                    act_mask, item_mask, space_mask = masks
                    print(f"\n[DEBUG Step {t}] Action Mask: {act_mask}")
                    print(f"Inventory: {inventory}")
                    if act_mask[2] == 1.0:
                        print("Crafting is VALID.")
                    else:
                        print("Crafting is BLOCKED.")

                # --- Time: Action Selection ---
                t_start = timeit.default_timer()
                epsilon = EPSILON_END + (EPSILON_START - EPSILON_END) * \
                          np.exp(-1. * env_steps_done / EPSILON_DECAY)
                last_epsilon = epsilon

                act, item, rot, map_idx, next_hidden = select_action(
                    policy_net, node_feats, H, hidden_state, epsilon, device,masks
                )

                # Convert Heatmap Index -> Norm Coords
                y_grid = map_idx // 17
                x_grid = map_idx % 17
                x_norm = -1.0 + (x_grid / 16.0) * 2.0
                y_norm = -1.0 + (y_grid / 16.0) * 2.0
                timer.record('action_select', timeit.default_timer() - t_start)

                # --- Time: Environment Step ---
                t_start = timeit.default_timer()
                next_obs, reward, done, _ = env.step(act, item, rot, x_norm, y_norm)
                timer.record('env_step', timeit.default_timer() - t_start)

                total_reward += reward

                # --- Time: Memory Push ---
                t_start = timeit.default_timer()
                if next_obs is not None:
                    action_tuple = (act, item, rot, map_idx)
                    memory.push((node_feats.cpu(), H.cpu()), action_tuple, reward,
                                (next_obs[0].cpu(), next_obs[1].cpu()), done)
                    hidden_state = next_hidden
                timer.record('memory_push', timeit.default_timer() - t_start)

                env_steps_done += 1
                steps_since_train += 1
                steps_since_report += 1

                # --- 4. BATCH & BURST TRAINING ---
                loss_val = 0.0

                if len(memory) > BATCH_SIZE and steps_since_train >= cfg.COLLECTION_STEPS:

                    for _ in range(cfg.TRAIN_EPOCHS):
                        # --- Time: Sample ---
                        t_start = timeit.default_timer()
                        transitions = memory.sample(BATCH_SIZE)
                        batch_state, batch_action, batch_reward, batch_next_state, batch_done = zip(*transitions)
                        timer.record('train_sample', timeit.default_timer() - t_start)

                        loss_total = 0

                        # Manual Batch Processing (Variable Graph Sizes)
                        for i in range(BATCH_SIZE):
                            s_nodes, s_H = batch_state[i]
                            a_act, a_item, a_rot, a_map = batch_action[i]
                            r = batch_reward[i]
                            ns_nodes, ns_H = batch_next_state[i]
                            d = batch_done[i]

                            # --- Time: To Device ---
                            t_start = timeit.default_timer()
                            s_nodes, s_H = s_nodes.to(device), s_H.to(device)
                            ns_nodes, ns_H = ns_nodes.to(device), ns_H.to(device)
                            dummy_h = (torch.zeros(1, cfg.LSTM_HIDDEN_DIM).to(device),
                                       torch.zeros(1, cfg.LSTM_HIDDEN_DIM).to(device))
                            timer.record('train_to_device', timeit.default_timer() - t_start)

                            # --- Time: Forward Policy ---
                            t_start = timeit.default_timer()
                            q_act_v, q_item_v, q_rot_v, q_map_v, _ = policy_net(s_nodes, s_H, dummy_h)
                            timer.record('train_forward_policy', timeit.default_timer() - t_start)

                            # --- Time: Forward Target ---
                            t_start = timeit.default_timer()
                            with torch.no_grad():
                                if d:
                                    target_val = r
                                else:
                                    nq_act, nq_item, nq_rot, nq_map, _ = target_net(ns_nodes, ns_H, dummy_h)
                                    max_q = (nq_act.max() + nq_item.max() + nq_rot.max() + nq_map.max()) / 4.0
                                    target_val = r + GAMMA * max_q
                            timer.record('train_forward_target', timeit.default_timer() - t_start)

                            # --- Time: Loss Compute ---
                            t_start = timeit.default_timer()
                            target_tensor = torch.tensor([target_val], device=device)
                            l1 = criterion(q_act_v[0, a_act].unsqueeze(0), target_tensor)
                            l2 = criterion(q_item_v[0, a_item].unsqueeze(0), target_tensor)
                            l3 = criterion(q_rot_v[0, a_rot].unsqueeze(0), target_tensor)
                            l4 = criterion(q_map_v.view(-1)[a_map].unsqueeze(0), target_tensor)
                            loss_total += (l1 + l2 + l3 + l4)
                            timer.record('train_loss_compute', timeit.default_timer() - t_start)

                        # --- Time: Backward ---
                        t_start = timeit.default_timer()
                        optimizer.zero_grad()
                        (loss_total / BATCH_SIZE).backward()
                        optimizer.step()
                        timer.record('train_backward', timeit.default_timer() - t_start)

                        loss_val = (loss_total / BATCH_SIZE).item()
                        updates_done += 1

                        episode_loss_accum += loss_val
                        episode_train_steps += 1

                        if updates_done % TARGET_UPDATE == 0:
                            target_net.load_state_dict(policy_net.state_dict())
                            tqdm.write(f"--> Updated Target Net at update {updates_done}")

                    steps_since_train = 0

                step_end_time = timeit.default_timer()
                step_duration = step_end_time - step_start_time
                step_times.append(step_duration)

                # === UPDATE INNER BAR with timing info ===
                inner_bar.set_postfix(
                    Rew=f"{total_reward:.1f}",
                    Eps=f"{epsilon:.2f}",
                    Loss=f"{loss_val:.2f}",
                    obs=f"{timer.last.get('obs_fetch', 0)*1000:.1f}ms",
                    env=f"{timer.last.get('env_step', 0)*1000:.1f}ms",
                    train=f"{timer.last.get('train_backward', 0)*1000:.0f}ms"
                )

                # === TIMING REPORT EVERY 1000 STEPS ===
                if steps_since_report >= 1000:
                    timer.print_report(steps_since_report)
                    timer.reset()
                    steps_since_report = 0

                if done:
                    break
        # === END OF EPISODE LOGGING ===
        avg_loss = episode_loss_accum / episode_train_steps if episode_train_steps > 0 else 0.0

        logger.log_episode(
            episode=episode + 1,
            step_count=env_steps_done,
            reward=total_reward,
            avg_loss=avg_loss,
            epsilon=last_epsilon,
            max_production=env.max_total_production_seen,
            max_edges=env.max_edges_seen,
            milestones=env.milestones
        )
        # === UPDATE OUTER BAR (End of episode stats) ===
        avg_ep_time = np.mean(step_times) if step_times else 0
        outer_bar.set_postfix(LastRew=f"{total_reward:.1f}", AvgTime=f"{avg_ep_time:.3f}s")

    # Final timing report
    if steps_since_report > 0:
        timer.print_report(steps_since_report)

    torch.save(policy_net.state_dict(), "jimbo_dqn_weights.pth")
    print("\nModel saved to jimbo_dqn_weights.pth")
    env.close()


if __name__ == "__main__":
    train()
