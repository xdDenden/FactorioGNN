import shutil
import time
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque, defaultdict
from tqdm import tqdm
import os
import traceback
import json
import docker
import Actor
import RunConfig
from RunConfig import *
from OrePatchDetector import OrePatchDetector
from environment import FactorioEnv
from FactorioHGNN import FactorioHGNN
from mappings import get_available_items
from plotting import TrainingLogger
from rcon_bridge.rcon_bridge import Rcon_reciever
from ActionMasking import get_action_masks
import timeit
import torch.multiprocessing as mp

# --- Hyperparameters ---
GAMMA = 0.99  # Discount factor for future rewards
LR = 1e-4  # Learning rate for the optimizer
BATCH_SIZE = 32  # Number of samples per training batch
BUFFER_SIZE = 50000  # Maximum size of the replay buffer
EPSILON_START = 1.0  # Initial value of epsilon for epsilon-greedy policy
EPSILON_END = 0.05  # Minimum value of epsilon for epsilon-greedy policy
EPSILON_DECAY = 563698  # Decay rate for epsilon over time
TARGET_UPDATE = 200  # Frequency of target network updates (in gradient steps)
NUM_EPISODES = 50  # Total number of episodes to train the model
AUTOSAVE_PATH = "autosave.pth"


#-- Docker Parameters
CONTAINER_NAME = "factorio"  # Name of the Factorio Docker container
SAVE_FOLDER = os.path.join(".", "factorio_data", "saves") # Path to the saves folder on the host machine
SAVES_POOL = "./SAVES_POOL" # Path to the saves we use to test the AI this will be within this project
UPDATE_INTERVAL_SEC = 5.0  # Update the dashboard JSON every 5 seconds
STATE_FILE = "dashboard_state.json"
os.makedirs(SAVE_FOLDER, exist_ok=True)

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
        print("\n" + "="*70)
        print(f"TIMING REPORT (Last {step_count} steps)")
        print("="*70)

        # Sort by total time descending
        sorted_ops = sorted(self.totals.items(), key=lambda x: -x[1])

        for name, total in sorted_ops:
            count = self.counts[name]
            avg_ms = (total / count * 1000) if count > 0 else 0
            print(f"  {name:<24}: avg={avg_ms:>8.2f}ms, total={total:>8.2f}s, count={count}")

        total_time = sum(self.totals.values())
        print("-"*70)
        print(f"  {'TOTAL':<24}: total={total_time:>8.2f}s")
        print("="*70 + "\n")


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
        act = random.choice(valid_actions) if len(valid_actions) > 0 else 0

        # 2. Select Item from valid indices FOR THAT ACTION
        # item_mask is [num_actions, num_items]
        valid_items = np.nonzero(item_mask[act])[0]
        item = random.choice(valid_items) if len(valid_items) > 0 else 0

        # 3. Select Rotation (Unmasked for now)
        rot = random.randint(0, 3)

        # 4. Select Heatmap Location from valid indices FOR THAT ACTION
        # space_mask is [num_actions, grid_size]
        valid_locs = np.nonzero(space_mask[act])[0]
        heatmap_idx = random.choice(valid_locs) if len(valid_locs) > 0 else 0

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

def dump_dashboard_state(state_dict):
    """Safely write state to JSON so Streamlit can read it."""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state_dict, f)
    except Exception:
        pass # Ignore write collisions

def dump_agent_state(agent_id, current_map, epsilon, step, episode_reward, total_actor_steps, steps_per_sec):
    """Safely write individual agent state for Streamlit tabs."""
    agent_file = f"agent_{agent_id}_state.json"
    state_dict = {
        "agent_id": agent_id,
        "current_map": current_map,
        "epsilon": epsilon,
        "step": step,
        "episode_reward": episode_reward,
        "total_actor_steps": total_actor_steps,
        "steps_per_sec": round(steps_per_sec, 2)
    }
    try:
        with open(agent_file, 'w') as f:
            json.dump(state_dict, f)
    except Exception:
        pass


def save_checkpoint(path, policy_net, target_net, optimizer, memory, total_steps_ingested, updates_done):
    print(f"\nSaving autosave to {path}...")
    torch.save({
        'policy_net': policy_net.state_dict(),
        'target_net': target_net.state_dict(),
        'optimizer': optimizer.state_dict(),
        'memory': memory.buffer,
        'total_steps_ingested': total_steps_ingested,
        'updates_done': updates_done
    }, path)
    print("Autosave complete.")

def load_checkpoint(path, policy_net, target_net, optimizer, memory):
    """Loads the training state from a file."""
    if not os.path.exists(path):
        return 0, 0

    print(f"Loading checkpoint from {path}...")
    try:
        checkpoint = torch.load(path, weights_only=False)
        policy_net.load_state_dict(checkpoint['policy_net'])
        target_net.load_state_dict(checkpoint['target_net'])
        optimizer.load_state_dict(checkpoint['optimizer'])
        memory.buffer = checkpoint['memory']
        return checkpoint.get('total_steps_ingested', 0), checkpoint.get('updates_done', 0)
    except Exception as e:
        print(f"Warning: Failed to load checkpoint (likely corrupted). Error: {e}")
        print("Starting with fresh weights.")
        return 0, 0


class MapScheduler:
    def __init__(self, pool_path):
        self.pool_path = pool_path
        self.queue = []

    def get_next_map(self):
        # Refill and shuffle if empty
        if not self.queue:
            print("Map queue empty. Refilling and shuffling...")
            # Filter for .zip to avoid system files like .DS_Store
            self.queue = [f for f in os.listdir(self.pool_path) if f.endswith('.zip')]
            random.shuffle(self.queue)

        return self.queue.pop()



    #main training loop


# ==========================================
# 1. THE ACTOR LOOP (Runs in multiple processes)
# ==========================================
def actor_loop(agent_id, shared_policy, exp_queue, device, cfg):
    print(f"[Actor {agent_id}] Booting up on {device}...")

    map_scheduler = MapScheduler(SAVES_POOL)
    actor = Actor.ActorWorker(agent_id)

    # --- Local Replica ---
    # To prevent lock contention, actors infer from a local copy.
    local_policy = FactorioHGNN(hidden_dim=cfg.HIDDEN_DIM, lstm_hidden_dim=cfg.LSTM_HIDDEN_DIM).to(device)

    CHUNK_SIZE = 32
    SYNC_INTERVAL = 128

    # Simple global step counter for epsilon decay
    actor_steps = 0

    # --- Timing trackers for Iterations / Sec ---
    last_log_time = time.time()
    last_log_steps = 0

    while True:
        try:
            target_save = map_scheduler.get_next_map()
            map_source_path = os.path.join(SAVES_POOL, target_save)

            patches = actor.prepare_map_and_ores(map_source_path)
            obs = actor.env.reset()
            if obs is None: continue

            patches = actor.env.current_patches
            hidden_state = (torch.zeros(1, cfg.LSTM_HIDDEN_DIM).to(device),
                            torch.zeros(1, cfg.LSTM_HIDDEN_DIM).to(device))

            local_buffer = []
            steps_since_sync = 0
            episode_reward = 0.0

            # Sync weights at the start of every episode
            local_policy.load_state_dict(shared_policy.state_dict())

            for t in range(cfg.MAX_TIMESTEPS):
                if t > 0:
                    obs = env._last_obs
                timer.record('obs_fetch', timeit.default_timer() - t_start)

                # Sync local weights with Learner periodically
                if steps_since_sync >= SYNC_INTERVAL:
                    local_policy.load_state_dict(shared_policy.state_dict())
                    steps_since_sync = 0

                node_feats, H = obs
                node_feats, H = node_feats.to(device), H.to(device)

                raw_entities = actor.env._last_raw_entities
                raw_player = actor.env._last_raw_player
                inv_list = raw_player.get('inventory', [])
                inventory = {item.get('name'): item.get('count', 0) for item in inv_list}
                valid_items = get_available_items(actor.env.receiver.scan_research())

                masks = get_action_masks(
                    entities=raw_entities, player_info=raw_player, inventory=inventory,
                    available_items=valid_items, bounds=actor.env.current_bounds,
                    patches=patches, move_state=actor.env.move_state
                )

                epsilon = max(EPSILON_END, EPSILON_START - (EPSILON_START - EPSILON_END) * (actor_steps / EPSILON_DECAY))

                # Infer from LOCAL policy
                act, item, rot, map_idx, next_hidden = select_action(
                    local_policy, node_feats, H, hidden_state, epsilon, device, masks
                )

                y_grid, x_grid = map_idx // 17, map_idx % 17
                x_norm, y_norm = -1.0 + (x_grid / 16.0) * 2.0, -1.0 + (y_grid / 16.0) * 2.0

                next_obs, reward, done, _ = actor.env.step(act, item, rot, x_norm, y_norm)
                episode_reward += reward

                if next_obs is not None:
                    s_nodes_cpu, s_H_cpu = node_feats.detach().cpu(), H.detach().cpu()
                    ns_nodes_cpu, ns_H_cpu = next_obs[0].detach().cpu(), next_obs[1].detach().cpu()
                    action_tuple = (act, item, rot, map_idx)

                    # Append to local chunk buffer
                    local_buffer.append((
                        (s_nodes_cpu, s_H_cpu), action_tuple, reward, (ns_nodes_cpu, ns_H_cpu), done
                    ))

                    # Push chunk to queue
                    if len(local_buffer) >= CHUNK_SIZE:
                        exp_queue.put(local_buffer)
                        local_buffer = []

                    hidden_state = next_hidden

                steps_since_sync += 1
                actor_steps += 1

                # --- Calculate Iterations / Sec and update dashboard ---
                if t % 50 == 0 or done:
                    current_time = time.time()
                    elapsed = current_time - last_log_time
                    steps_diff = actor_steps - last_log_steps
                    steps_per_sec = steps_diff / elapsed if elapsed > 0 else 0.0

                    dump_agent_state(agent_id, target_save, epsilon, t, episode_reward, actor_steps, steps_per_sec)

                    last_log_time = current_time
                    last_log_steps = actor_steps

                if done:
                    break

            # Empty remaining buffer at end of episode
            if len(local_buffer) > 0:
                exp_queue.put(local_buffer)

        except Exception as e:
            print(f"[Actor {agent_id}] Crashed: {e}. Restarting environment...")
            time.sleep(5)


def learner_loop(shared_policy, exp_queue, device, cfg, num_actors):
    print(f"[Learner] Starting up on {device}...")

    # --- GPU Models ---
    policy_net = FactorioHGNN(hidden_dim=cfg.HIDDEN_DIM, lstm_hidden_dim=cfg.LSTM_HIDDEN_DIM).to(device)
    policy_net.load_state_dict(shared_policy.state_dict())  # Init from CPU

    target_net = FactorioHGNN(hidden_dim=cfg.HIDDEN_DIM, lstm_hidden_dim=cfg.LSTM_HIDDEN_DIM).to(device)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()

    optimizer = optim.Adam(policy_net.parameters(), lr=LR)
    criterion = nn.MSELoss()
    memory = ReplayBuffer(BUFFER_SIZE)
    criterion = nn.MSELoss()

    updates_done = 0
    total_steps_ingested = 0
    updates_done = 0

    if os.path.exists(AUTOSAVE_PATH):
        total_steps_ingested, updates_done = load_checkpoint(AUTOSAVE_PATH, policy_net, target_net, optimizer, memory)
    else:
        policy_net.load_state_dict(shared_policy.state_dict())
        target_net.load_state_dict(policy_net.state_dict())

    target_net.eval()

    MIN_BUFFER_SIZE = BATCH_SIZE * 5

    last_json_update = time.time()
    last_updates_count = updates_done
    start_time_total = time.time()

    hyperparameters = {k: v for k, v in vars(cfg).items() if not k.startswith('_')}

    while True:
        # 1. Unroll the queue chunks into the Replay Buffer
        while not exp_queue.empty():
            try:
                chunk = exp_queue.get_nowait()
                for transition in chunk:
                    memory.push(*transition)
                    total_steps_ingested += 1
            except Exception:
                break  # Queue empty or busy

        # 2. Train if we have enough data
        if len(memory) >= MIN_BUFFER_SIZE:
            transitions = memory.sample(BATCH_SIZE)
            batch_state, batch_action, batch_reward, batch_next_state, batch_done = zip(*transitions)

            loss_total = 0

            for i in range(BATCH_SIZE):
                s_nodes, s_H = batch_state[i]
                a_act, a_item, a_rot, a_map = batch_action[i]
                r = batch_reward[i]
                ns_nodes, ns_H = batch_next_state[i]
                d = batch_done[i]

                # Move to GPU
                s_nodes, s_H = s_nodes.to(device), s_H.to(device)
                ns_nodes, ns_H = ns_nodes.to(device), ns_H.to(device)

                dummy_h = (torch.zeros(1, cfg.LSTM_HIDDEN_DIM).to(device),
                           torch.zeros(1, cfg.LSTM_HIDDEN_DIM).to(device))

                # Forward pass on ACTUAL policy net
                q_act_v, q_item_v, q_rot_v, q_map_v, _ = policy_net(s_nodes, s_H, dummy_h)

                with torch.no_grad():
                    if d:
                        target_val = r
                    else:
                        nq_act, nq_item, nq_rot, nq_map, _ = target_net(ns_nodes, ns_H, dummy_h)
                        max_q = (nq_act.max() + nq_item.max() + nq_rot.max() + nq_map.max()) / 4.0
                        target_val = r + GAMMA * max_q

                target_tensor = torch.tensor([target_val], device=device)
                l1 = criterion(q_act_v[0, a_act].unsqueeze(0), target_tensor)
                l2 = criterion(q_item_v[0, a_item].unsqueeze(0), target_tensor)
                l3 = criterion(q_rot_v[0, a_rot].unsqueeze(0), target_tensor)
                l4 = criterion(q_map_v.view(-1)[a_map].unsqueeze(0), target_tensor)
                loss_total += (l1 + l2 + l3 + l4)

            # Backprop
            optimizer.zero_grad()
            (loss_total / BATCH_SIZE).backward()
            torch.nn.utils.clip_grad_norm_(policy_net.parameters(), max_norm=1.0)
            optimizer.step()

            updates_done += 1
            current_loss = (loss_total / BATCH_SIZE).item()

            # 3. Target Update & CPU Weight Push
            if updates_done % TARGET_UPDATE == 0:
                target_net.load_state_dict(policy_net.state_dict())

                # PUSH WEIGHTS TO CPU FOR ACTORS TO PULL
                shared_policy.load_state_dict({k: v.cpu() for k, v in policy_net.state_dict().items()})
                print(f"[Learner] Target updated & weights synced to CPU at {updates_done} updates. Loss: {current_loss:.4f}")

                # Example Dashboard Update / Checkpointing trigger
                current_time = time.time()
                if current_time - last_json_update > UPDATE_INTERVAL_SEC:
                    elapsed_tot = current_time - start_time_total
                    updates_per_sec = (updates_done - last_updates_count) / (current_time - last_json_update)

                    state_dict = {
                        "steps_ingested": total_steps_ingested,
                        "updates_done": updates_done,
                        "buffer_size": len(memory),
                        "current_loss": round(current_loss, 4),
                        "updates_per_sec": round(updates_per_sec, 2),
                        "elapsed_total": elapsed_tot,
                        "hyperparameters": hyperparameters,
                        "num_actors": num_actors
                    }
                    dump_dashboard_state(state_dict)

                    last_json_update = current_time
                    last_updates_count = updates_done

                    # Autosave periodically
                    if updates_done % (TARGET_UPDATE * 10) == 0:
                        save_checkpoint(AUTOSAVE_PATH, policy_net, target_net, optimizer, memory, total_steps_ingested, updates_done)


if __name__ == '__main__':
    mp.set_start_method('spawn', force=True)

    cfg = Config()

    cpu_device = torch.device("cpu")
    if torch.cuda.is_available():
        gpu_device = torch.device("cuda")
    else:
        gpu_device = torch.device("cpu")

    print(f"Master process starting. Learner on: {gpu_device}, Actors on: {cpu_device}")

    shared_policy_net = FactorioHGNN(hidden_dim=cfg.HIDDEN_DIM, lstm_hidden_dim=cfg.LSTM_HIDDEN_DIM).to(cpu_device)
    shared_policy_net.share_memory()

    experience_queue = mp.Queue(maxsize=2000)

    NUM_ACTORS = 3
    actor_processes = []

    # 1. Start ALL actor processes first
    for i in range(NUM_ACTORS):
        p = mp.Process(target=actor_loop, args=(i, shared_policy_net, experience_queue, cpu_device, cfg))
        p.start()
        actor_processes.append(p)

    # 2. THEN start the learner loop on the main thread
    try:
        learner_loop(shared_policy_net, experience_queue, gpu_device, cfg, NUM_ACTORS)
    except KeyboardInterrupt:
        print("\nShutting down workers...")
        for p in actor_processes:
            p.terminate()
        for p in actor_processes:
            p.join()
        print("Shutdown complete.")