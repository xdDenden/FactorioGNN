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
from RunConfig import Config
from OrePatchDetector import OrePatchDetector
from environment import FactorioEnv
from FactorioHGNN import FactorioHGNN
from mappings import get_available_items
from plotting import TrainingLogger
from rcon_bridge.rcon_bridge import Rcon_reciever
from ActionMasking import get_action_masks
import timeit
import torch.multiprocessing as mp

# Initialize config globally so helper functions have access
cfg = Config()

# Make sure our save folder exists
os.makedirs(cfg.SAVE_FOLDER, exist_ok=True)

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

        h_next = (torch.zeros(1, cfg.HIDDEN_DIM).to(device), torch.zeros(1, cfg.HIDDEN_DIM).to(device))
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
        with open(cfg.STATE_FILE, 'w') as f:
            json.dump(state_dict, f)
    except Exception:
        pass # Ignore write collisions

def dump_actor_state(actor_id, current_map, epsilon, step, episode_reward, total_actor_steps, steps_per_sec):
    """Safely write individual actor state for Streamlit tabs."""
    actor_file = f"actor_{actor_id}_state.json"
    state_dict = {
        "actor_id": actor_id,
        "current_map": current_map,
        "epsilon": epsilon,
        "step": step,
        "episode_reward": episode_reward,
        "total_actor_steps": total_actor_steps,
        "steps_per_sec": round(steps_per_sec, 2)
    }
    try:
        with open(actor_file, 'w') as f:
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
def actor_loop(actor_id, shared_policy, exp_queue, device, cfg):
    torch.set_num_threads(1)
    print(f"[Actor {actor_id}] Booting up on {device}...")

    map_scheduler = MapScheduler(cfg.SAVES_POOL)
    actor = Actor.ActorWorker(actor_id)

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

    try:
        while True:
            try:
                target_save = map_scheduler.get_next_map()
                map_source_path = os.path.join(cfg.SAVES_POOL, target_save)

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
                        obs = actor.env._last_obs

                    if steps_since_sync >= cfg.SYNC_INTERVAL:
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

                    epsilon = max(cfg.EPSILON_END, cfg.EPSILON_START - (cfg.EPSILON_START - cfg.EPSILON_END) * (actor_steps / cfg.EPSILON_DECAY))

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

                        if len(local_buffer) >= cfg.CHUNK_SIZE:
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

                        dump_actor_state(actor_id, target_save, epsilon, t, episode_reward, actor_steps, steps_per_sec)

                        last_log_time = current_time
                        last_log_steps = actor_steps

                    if done:
                        break

                # Empty remaining buffer at end of episode
                if len(local_buffer) > 0:
                    exp_queue.put(local_buffer)

            except Exception as e:
                print(f"[Actor {actor_id}] Crashed: {e}. Restarting environment...")
                time.sleep(5)
    except KeyboardInterrupt:
        print(f"[Actor {actor_id}] Received shutdown signal.")
    finally:
        actor.stop()


# ==========================================
# 2. THE LEARNER LOOP (Runs on Main Thread)
# ==========================================
def learner_loop(shared_policy, exp_queue, device, cfg):
    print(f"[Learner] Starting up on {device}...")

    # --- GPU Models ---
    policy_net = FactorioHGNN(hidden_dim=cfg.HIDDEN_DIM, lstm_hidden_dim=cfg.LSTM_HIDDEN_DIM).to(device)
    policy_net.load_state_dict(shared_policy.state_dict())  # Init from CPU

    target_net = FactorioHGNN(hidden_dim=cfg.HIDDEN_DIM, lstm_hidden_dim=cfg.LSTM_HIDDEN_DIM).to(device)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()

    optimizer = optim.Adam(policy_net.parameters(), lr=cfg.LR)
    criterion = nn.MSELoss()
    memory = ReplayBuffer(cfg.BUFFER_SIZE)

    updates_done = 0
    total_steps_ingested = 0

    if os.path.exists(cfg.AUTOSAVE_PATH):
        total_steps_ingested, updates_done = load_checkpoint(cfg.AUTOSAVE_PATH, policy_net, target_net, optimizer, memory)
    else:
        policy_net.load_state_dict(shared_policy.state_dict())
        target_net.load_state_dict(policy_net.state_dict())

    target_net.eval()

    MIN_BUFFER_SIZE = cfg.BATCH_SIZE * 5

    last_json_update = time.time()
    last_updates_count = updates_done
    start_time_total = time.time()
    last_steps_ingested = total_steps_ingested

    hyperparameters = {k: v for k, v in vars(cfg).items() if not k.startswith('_')}

    while True:
        # 1. Unroll the queue chunks into the Replay Buffer
        chunks_unrolled = 0
        max_chunks_per_step = 40
        while not exp_queue.empty() and chunks_unrolled < max_chunks_per_step:
            try:
                chunk = exp_queue.get_nowait()
                for transition in chunk:
                    memory.push(*transition)
                    total_steps_ingested += 1
                chunks_unrolled += 1
            except Exception:
                break  # Queue empty or busy

        if len(memory) >= cfg.MIN_BUFFER_SIZE:
            transitions = memory.sample(cfg.BATCH_SIZE)
            batch_state, batch_action, batch_reward, batch_next_state, batch_done = zip(*transitions)

            # --- 1. Find Max Dimensions for Current Batch ---
            max_nodes = max(state[0].shape[0] for state in batch_state)
            max_edges = max(state[1].shape[1] for state in batch_state)

            max_next_nodes = max(n_state[0].shape[0] for n_state in batch_next_state)
            max_next_edges = max(n_state[1].shape[1] for n_state in batch_next_state)

            # --- 2. Dynamically Infer Feature Dimension ---
            feature_dim = batch_state[0][0].shape[1]

            batched_s_nodes = torch.zeros((cfg.BATCH_SIZE, max_nodes, feature_dim), device=device)
            batched_s_H = torch.zeros((cfg.BATCH_SIZE, max_nodes, max_edges), device=device)
            node_masks = torch.zeros((cfg.BATCH_SIZE, max_nodes), dtype=torch.bool, device=device)

            batched_ns_nodes = torch.zeros((cfg.BATCH_SIZE, max_next_nodes, feature_dim), device=device)
            batched_ns_H = torch.zeros((cfg.BATCH_SIZE, max_next_nodes, max_next_edges), device=device)
            next_node_masks = torch.zeros((cfg.BATCH_SIZE, max_next_nodes), dtype=torch.bool, device=device)

            for i in range(cfg.BATCH_SIZE):
                s_nodes, s_H = batch_state[i]
                n_nodes, n_edges = s_H.shape
                batched_s_nodes[i, :n_nodes, :] = s_nodes.to(device)
                batched_s_H[i, :n_nodes, :n_edges] = s_H.to(device)
                node_masks[i, :n_nodes] = True

                # Next State
                ns_nodes, ns_H = batch_next_state[i]
                nn_nodes, nn_edges = ns_H.shape
                batched_ns_nodes[i, :nn_nodes, :] = ns_nodes.to(device)
                batched_ns_H[i, :nn_nodes, :nn_edges] = ns_H.to(device)
                next_node_masks[i, :nn_nodes] = True

            dummy_h = (torch.zeros(cfg.BATCH_SIZE, cfg.LSTM_HIDDEN_DIM, device=device),
                       torch.zeros(cfg.BATCH_SIZE, cfg.LSTM_HIDDEN_DIM, device=device))

            # --- 5. ONE MASSIVE FORWARD PASS ---
            q_act_v, q_item_v, q_rot_v, q_map_v, _ = policy_net(batched_s_nodes, batched_s_H, dummy_h, mask=node_masks)

            with torch.no_grad():
                nq_act, nq_item, nq_rot, nq_map, _ = target_net(batched_ns_nodes, batched_ns_H, dummy_h, mask=next_node_masks)

                # Vectorized Max Q-value extraction
                max_nq_act = nq_act.max(dim=1)[0]
                max_nq_item = nq_item.max(dim=1)[0]
                max_nq_rot = nq_rot.max(dim=1)[0]
                max_nq_map = nq_map.view(cfg.BATCH_SIZE, -1).max(dim=1)[0]

                max_q = (max_nq_act + max_nq_item + max_nq_rot + max_nq_map) / 4.0

                r_tensor = torch.tensor(batch_reward, dtype=torch.float32, device=device)
                d_tensor = torch.tensor(batch_done, dtype=torch.float32, device=device)

                target_vals = r_tensor + cfg.GAMMA * max_q * (1 - d_tensor)

            # --- 6. VECTORIZED LOSS CALCULATION ---
            actions_t = torch.tensor(batch_action, dtype=torch.long, device=device)
            act_idx = actions_t[:, 0]
            item_idx = actions_t[:, 1]
            rot_idx = actions_t[:, 2]
            map_idx = actions_t[:, 3]

            batch_arange = torch.arange(cfg.BATCH_SIZE, device=device)

            chosen_q_act = q_act_v[batch_arange, act_idx]
            chosen_q_item = q_item_v[batch_arange, item_idx]
            chosen_q_rot = q_rot_v[batch_arange, rot_idx]
            chosen_q_map = q_map_v.view(cfg.BATCH_SIZE, -1)[batch_arange, map_idx]

            loss = (criterion(chosen_q_act, target_vals) +
                    criterion(chosen_q_item, target_vals) +
                    criterion(chosen_q_rot, target_vals) +
                    criterion(chosen_q_map, target_vals))

            # --- 7. BACKPROPAGATION ---
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(policy_net.parameters(), max_norm=1.0)
            optimizer.step()

            updates_done += 1
            current_loss = loss.item()

            # --- 8. TARGET UPDATE & SYNC ---
            if updates_done % cfg.TARGET_UPDATE == 0:
                target_net.load_state_dict(policy_net.state_dict())
                shared_policy.load_state_dict({k: v.cpu() for k, v in policy_net.state_dict().items()})
                print(f"[Learner] Target updated & weights synced to CPU at {updates_done} updates. Loss: {current_loss:.4f}")

                # --- 9. DASHBOARD UPDATE ---
                current_time = time.time()
                if current_time - last_json_update > cfg.UPDATE_INTERVAL_SEC:
                    elapsed_interval = current_time - last_json_update
                    elapsed_tot = current_time - start_time_total

                    # Calculate rates for the interval
                    updates_in_interval = updates_done - last_updates_count
                    updates_per_sec = updates_in_interval / elapsed_interval

                    # You will need to add `last_steps_ingested = 0` up where you define last_updates_count!
                    steps_in_interval = total_steps_ingested - last_steps_ingested
                    ingestion_rate = steps_in_interval / elapsed_interval

                    # GPU Processing Rate (Samples per second)
                    training_rate = updates_per_sec * cfg.BATCH_SIZE

                    # UTD Ratio (How many training samples processed per 1 new environment step)
                    utd_ratio = training_rate / ingestion_rate if ingestion_rate > 0 else 0.0

                    # since macos isnt fully implemented we gotta do this
                    try:
                        current_qsize = exp_queue.qsize()
                    except NotImplementedError:
                        current_qsize = "N/A on Mac"

                    state_dict = {
                        "steps_ingested": total_steps_ingested,
                        "updates_done": updates_done,
                        "buffer_size": len(memory),
                        "queue_size": current_qsize,
                        "current_loss": round(current_loss, 4),
                        "updates_per_sec": round(updates_per_sec, 2),
                        "ingestion_rate": round(ingestion_rate, 2),
                        "training_rate": round(training_rate, 2),
                        "utd_ratio": round(utd_ratio, 2),
                        "elapsed_total": elapsed_tot,
                        "hyperparameters": hyperparameters,
                        "num_actors": cfg.NUM_ACTORS
                    }

                    dump_dashboard_state(state_dict)

                    last_json_update = current_time
                    last_updates_count = updates_done
                    last_steps_ingested = total_steps_ingested

                    #Autosave every once in a while
                    if updates_done % (cfg.TARGET_UPDATE * 10) == 0:
                        save_checkpoint(cfg.AUTOSAVE_PATH, policy_net, target_net, optimizer, memory, total_steps_ingested, updates_done)


# this line should make sure that any not implemented MPS operations will throw CPU fallback errors instead of crashing the process
# this should make it carry on the operation on the cpu
# since i dont know what specific operation might happen and cant fix a not implemented error cus im NOT like that
# we just use this line instead
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

if __name__ == '__main__':
    mp.set_start_method('spawn', force=True)

    # cfg already instantiated at module level above
    cpu_device = torch.device("cpu")
    if torch.cuda.is_available():
        gpu_device = torch.device("cuda")
    elif torch.backends.mps.is_available():
        gpu_device = torch.device("mps")
    else:
        gpu_device = torch.device("cpu")

    print(f"Master process starting. Learner on: {gpu_device}, Actors on: {cpu_device}")

    shared_policy_net = FactorioHGNN(hidden_dim=cfg.HIDDEN_DIM, lstm_hidden_dim=cfg.LSTM_HIDDEN_DIM).to(cpu_device)
    shared_policy_net.share_memory()

    experience_queue = mp.Queue(maxsize=5000)

    actor_processes = []

    # Start ALL actor processes based on Config
    for i in range(cfg.NUM_ACTORS):
        p = mp.Process(target=actor_loop, args=(i, shared_policy_net, experience_queue, cpu_device, cfg))
        p.start()
        actor_processes.append(p)

    # 2. THEN start the learner loop on the main thread
    try:
        learner_loop(shared_policy_net, experience_queue, gpu_device, cfg)
    except KeyboardInterrupt:
        print("\n[Master] Ctrl+C detected. Asking Actors to pack up and delete their containers...")

        # We DO NOT use p.terminate() here anymore.
        # We wait for the Actors to run their `finally` blocks and close themselves.
        for p in actor_processes:
            p.join(timeout=10)  # Give them up to 10 seconds to delete the containers

        # If any actor is totally frozen and didn't shut down after 10 seconds, THEN execute them
        for p in actor_processes:
            if p.is_alive():
                print(f"[Master] Force terminating stuck process: {p.name}")
                p.terminate()

        print("[Master] All containers deleted. Shutdown complete.")