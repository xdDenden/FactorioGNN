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
import glob


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
    Epsilon-Greedy with Action Masking and Item conditioned Build Spatial Masking.
    Always advances the LSTM hidden_state even on random exploratory steps.
    """
    act_mask, item_mask, space_mask, *extra = masks
    build_spatial_by_item = extra[0] if extra else {}

    with torch.no_grad():
        q_act, q_item, q_rot, q_map, h_next = model(node_feats, H, hidden_state)

    if random.random() < epsilon:
        valid_actions = np.nonzero(act_mask)[0]
        act = int(random.choice(valid_actions)) if len(valid_actions) > 0 else 0

        # 2. Select Item from valid indices FOR THAT ACTION
        # item_mask is [num_actions, num_items]
        valid_items = np.nonzero(item_mask[act])[0]
        item = int(random.choice(valid_items)) if len(valid_items) > 0 else 0

        # 3. Select Rotation (Unmasked for now)
        rot = random.randint(0, 3)

        active_space_mask = build_spatial_by_item.get(item, space_mask[act]) if act == 3 else space_mask[act]
        valid_locs = np.nonzero(active_space_mask)[0]
        heatmap_idx = int(random.choice(valid_locs)) if len(valid_locs) > 0 else 0

        return act, item, rot, heatmap_idx, h_next
    else:
            masked_q_act = apply_mask_to_logits(q_act.view(-1), act_mask)
            act = masked_q_act.argmax().item()

            masked_q_item = apply_mask_to_logits(q_item.view(-1), item_mask[act])
            item = masked_q_item.argmax().item()

            rot = q_rot.argmax().item()

    active_space_mask = build_spatial_by_item.get(item, space_mask[act]) if act == 3 else space_mask[act]
    masked_q_map = apply_mask_to_logits(q_map.view(-1), active_space_mask)
    heatmap_idx = masked_q_map.argmax().item()

    return act, item, rot, heatmap_idx, h_next

def dump_dashboard_state(state_dict):
    """Safely write state to JSON so Streamlit can read it."""
    try:
        with open(cfg.STATE_FILE, 'w') as f:
            json.dump(state_dict, f)
    except Exception:
        pass # Ignore write collisions

def dump_actor_state(actor_id, current_map, epsilon, step, episode_reward, total_actor_steps, steps_per_sec,
                     reward_breakdown=None, episode=1, episodes_completed=0):
    """Safely write individual actor state for Streamlit tabs."""
    actor_file = f"actor_{actor_id}_state.json"
    state_dict = {
        "actor_id": actor_id,
        "current_map": current_map,
        "epsilon": epsilon,
        "step": step,
        "episode": episode,  # 1-based number of the episode currently being played
        "episodes_completed": episodes_completed,
        "episode_reward": episode_reward,
        "total_actor_steps": total_actor_steps,
        "steps_per_sec": round(steps_per_sec, 2),
        "reward_breakdown": reward_breakdown or {}
    }
    try:
        with open(actor_file, 'w') as f:
            json.dump(state_dict, f)
    except Exception:
        pass


def _atomic_torch_save(obj, target_path):
    """Writes to a .tmp file first and atomically renames so interrupted saves never corrupt existing files."""
    tmp_path = f"{target_path}.tmp"
    torch.save(obj, tmp_path)
    os.replace(tmp_path, target_path)


def _prune_old_files(pattern, max_keep):
    """Keeps only the `max_keep` most recent files matching `pattern`."""
    if max_keep <= 0:
        return
    files = sorted(glob.glob(pattern), key=os.path.getmtime)
    while len(files) > max_keep:
        oldest = files.pop(0)
        try:
            os.remove(oldest)
        except OSError:
            pass


def save_checkpoint(base_path, policy_net, target_net, optimizer, memory, total_steps_ingested, updates_done, cfg):
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    # 1. Rolling Full Checkpoint (autosave_<updates>_<timestamp>.pth)
    stem, ext = os.path.splitext(base_path)
    rolling_ckpt_path = f"{stem}_u{updates_done}_{timestamp}{ext}"
    print(f"\n[Autosave] Saving rolling checkpoint to {rolling_ckpt_path}...")

    ckpt_data = {
        'policy_net': policy_net.state_dict(),
        'target_net': target_net.state_dict(),
        'optimizer': optimizer.state_dict(),
        'memory': memory.buffer,
        'total_steps_ingested': total_steps_ingested,
        'updates_done': updates_done
    }
    _atomic_torch_save(ckpt_data, rolling_ckpt_path)
    # Also update the latest pointer file atomically for quick access
    _atomic_torch_save(ckpt_data, base_path)
    _prune_old_files(f"{stem}_u*{ext}", getattr(cfg, 'NUM_AUTOSAVES', 5))

    # 2. Rolling Weights-Only File (jimbo_dqn_weights_<updates>_<timestamp>.pth)
    weights_base = getattr(cfg, 'WEIGHTS_PATH', 'jimbo_dqn_weights.pth')
    w_stem, w_ext = os.path.splitext(weights_base)
    rolling_weights_path = f"{w_stem}_u{updates_done}_{timestamp}{w_ext}"
    print(f"[Autosave] Saving rolling weights to {rolling_weights_path}...")

    cpu_weights = {k: v.cpu() for k, v in policy_net.state_dict().items()}
    _atomic_torch_save(cpu_weights, rolling_weights_path)
    _atomic_torch_save(cpu_weights, weights_base)
    _prune_old_files(f"{w_stem}_u*{w_ext}", getattr(cfg, 'NUM_WEIGHTAUTOSAVE', 5))

    print("[Autosave] Rolling autosave & weights export complete.\n")


def load_checkpoint(base_path, policy_net, target_net, optimizer, memory):
    """Loads the newest valid rolling checkpoint, automatically falling back if the latest is corrupted."""
    stem, ext = os.path.splitext(base_path)
    candidates = sorted(glob.glob(f"{stem}_u*{ext}"), key=os.path.getmtime, reverse=True)
    if os.path.exists(base_path):
        candidates.append(base_path)

    if not candidates:
        return 0, 0

    for path in candidates:
        print(f"Attempting to load checkpoint from {path}...")
        try:
            checkpoint = torch.load(path, weights_only=False)
            policy_net.load_state_dict(checkpoint['policy_net'])
            target_net.load_state_dict(checkpoint['target_net'])
            optimizer.load_state_dict(checkpoint['optimizer'])
            memory.buffer = checkpoint['memory']
            print(f"Successfully loaded checkpoint: {path}")
            return checkpoint.get('total_steps_ingested', 0), checkpoint.get('updates_done', 0)
        except Exception as e:
            print(f"Warning: Failed to load {path} (Error: {e}). Trying previous backup...")

    print("All checkpoint candidates failed or were corrupted. Starting with fresh weights.")
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

STOP_TRAIN_FILE = ".stop_train"

def should_stop():
    """Checks if the Streamlit UI requested a graceful stop."""
    return os.path.exists(STOP_TRAIN_FILE)

# 1. THE ACTOR LOOP (Runs in multiple processes)
# Replace actor_loop and learner_loop in train_dqn.py (Lines 268-595)

def actor_loop(actor_id, shared_policy, exp_queue, device, cfg, initial_steps=0):
    print(f"[Actor {actor_id}] Booting up on {device}...")

    map_scheduler = MapScheduler(cfg.SAVES_POOL)
    actor = Actor.ActorWorker(actor_id)
    local_policy = FactorioHGNN(hidden_dim=cfg.HIDDEN_DIM, lstm_hidden_dim=cfg.LSTM_HIDDEN_DIM).to(device)
    local_policy.eval()

    actor_steps = initial_steps
    last_log_time = time.time()
    last_log_steps = actor_steps
    episodes_completed = 0

    # Each actor runs cfg.NUM_EPISODES episodes (matches StreamlitUpdate.py telemetry)
    max_episodes = getattr(cfg, 'NUM_EPISODES', 2)

    try:
        while episodes_completed < max_episodes and not should_stop():
            try:
                target_save = map_scheduler.get_next_map()
                map_source_path = os.path.join(cfg.SAVES_POOL, target_save)

                if should_stop():
                    break

                actor.prepare_map_and_ores(map_source_path)
                if should_stop():
                    break

                obs = actor.env.reset()
                if obs is None:
                    continue

                patches = actor.env.current_patches
                hidden_state = (torch.zeros(1, cfg.LSTM_HIDDEN_DIM, device=device),
                                torch.zeros(1, cfg.LSTM_HIDDEN_DIM, device=device))

                local_buffer = []
                steps_since_sync = 0
                episode_reward = 0.0

                local_policy.load_state_dict(shared_policy.state_dict())

                valid_items = []

                for t in range(cfg.MAX_TIMESTEPS):
                    if should_stop():
                        print(f"[Actor {actor_id}] Stop signal detected. Aborting episode cleanly...")
                        break

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

                    # 1. Protect scan_research RCON call
                    if t == 0 or t % 50 == 0:
                        try:
                            valid_items = get_available_items(actor.env.receiver.scan_research())
                        except Exception as res_err:
                            print(f"\n[Actor {actor_id}] scan_research failed at step {t}: {res_err}. Reconnecting RCON...")
                            try:
                                actor.env.receiver.disconnect()
                                time.sleep(1.0)
                                actor.env.receiver.connect()
                                valid_items = get_available_items(actor.env.receiver.scan_research())
                            except Exception as recon_err:
                                print(f"[Actor {actor_id}] RCON reconnect failed ({recon_err}), aborting episode.")
                                break

                    masks = get_action_masks(
                        entities=raw_entities, player_info=raw_player, inventory=inventory,
                        available_items=valid_items, bounds=actor.env.current_bounds,
                        patches=patches, move_state=actor.env.move_state
                    )

                    epsilon = max(
                        cfg.EPSILON_END,
                        cfg.EPSILON_START - (cfg.EPSILON_START - cfg.EPSILON_END) * (actor_steps / cfg.EPSILON_DECAY)
                    )

                    act, item, rot, map_idx, next_hidden = select_action(
                        local_policy, node_feats, H, hidden_state, epsilon, device, masks
                    )

                    y_grid, x_grid = map_idx // 17, map_idx % 17
                    x_norm = -1.0 + (x_grid / 16.0) * 2.0
                    y_norm = -1.0 + (y_grid / 16.0) * 2.0

                    # 2. Protect env.step RCON call
                    try:
                        next_obs, reward, done, info = actor.env.step(act, item, rot, x_norm, y_norm)
                    except Exception as step_err:
                        print(f"\n[Actor {actor_id}] Transient error at step {t}: {step_err}. Reconnecting RCON...")
                        traceback.print_exc()
                        try:
                            actor.env.receiver.disconnect()
                            time.sleep(1.0)
                            actor.env.receiver.connect()
                        except Exception as recon_err:
                            print(f"[Actor {actor_id}] RCON reconnect failed ({recon_err}), aborting episode.")
                            break
                        continue

                    episode_reward += reward

                    if next_obs is not None:
                        s_nodes_cpu, s_H_cpu = node_feats.detach().cpu(), H.detach().cpu()
                        ns_nodes_cpu, ns_H_cpu = next_obs[0].detach().cpu(), next_obs[1].detach().cpu()
                        h_cpu = (hidden_state[0].detach().cpu(), hidden_state[1].detach().cpu())
                        nh_cpu = (next_hidden[0].detach().cpu(), next_hidden[1].detach().cpu())
                        action_tuple = (act, item, rot, map_idx)

                        local_buffer.append((
                            (s_nodes_cpu, s_H_cpu, h_cpu),
                            action_tuple,
                            reward,
                            (ns_nodes_cpu, ns_H_cpu, nh_cpu),
                            done
                        ))

                        if len(local_buffer) >= cfg.CHUNK_SIZE:
                            exp_queue.put(local_buffer)
                            local_buffer = []

                        hidden_state = next_hidden

                    steps_since_sync += 1
                    actor_steps += 1

                    # Calculate Iterations / Sec and update dashboard
                    if t % 50 == 0 or done:
                        current_time = time.time()
                        elapsed = current_time - last_log_time
                        steps_diff = actor_steps - last_log_steps
                        steps_per_sec = steps_diff / elapsed if elapsed > 0 else 0.0

                        dump_actor_state(actor_id, target_save, epsilon, t, episode_reward, actor_steps, steps_per_sec,
                                         reward_breakdown=info.get("reward_breakdown", {}),
                                         episode=episodes_completed + 1,
                                         episodes_completed=episodes_completed)

                        last_log_time = current_time
                        last_log_steps = actor_steps

                    if done:
                        break

                    if should_stop():
                        break

                if len(local_buffer) > 0:
                    exp_queue.put(local_buffer)

                episodes_completed += 1
                dump_actor_state(actor_id, target_save, epsilon, 0, 0.0, actor_steps, 0.0,
                                 reward_breakdown={},
                                 episode=episodes_completed + 1,
                                 episodes_completed=episodes_completed)

            except Exception as e:
                if should_stop():
                    break
                print(f"\n[Actor {actor_id}] CRASHED: {e}")
                if actor.container is not None:
                    try:
                        print(actor.container.logs(tail=20).decode('utf-8'))
                    except Exception:
                        pass
                print(f"[Actor {actor_id}] Restarting environment...\n")
                time.sleep(5)
    except KeyboardInterrupt:
        print(f"[Actor {actor_id}] Received shutdown signal.")
    finally:
        actor.stop()

#TODO: Readd comments from earlier commit

# 2. THE LEARNER LOOP (Runs on Main Thread)
def learner_loop(shared_policy, exp_queue, device, cfg, actor_processes):
    print(f"[Learner] Starting up on {device}...")

    policy_net = FactorioHGNN(hidden_dim=cfg.HIDDEN_DIM, lstm_hidden_dim=cfg.LSTM_HIDDEN_DIM).to(device)
    policy_net.load_state_dict(shared_policy.state_dict())

    target_net = FactorioHGNN(hidden_dim=cfg.HIDDEN_DIM, lstm_hidden_dim=cfg.LSTM_HIDDEN_DIM).to(device)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()

    optimizer = optim.Adam(policy_net.parameters(), lr=cfg.LR)
    memory = ReplayBuffer(cfg.BUFFER_SIZE)

    total_steps_ingested, updates_done = load_checkpoint(
        cfg.AUTOSAVE_PATH, policy_net, target_net, optimizer, memory
    )
    if updates_done > 0:
        shared_policy.load_state_dict({k: v.cpu() for k, v in policy_net.state_dict().items()})
    else:
        policy_net.load_state_dict(shared_policy.state_dict())
        target_net.load_state_dict(policy_net.state_dict())

    target_net.eval()

    last_json_update = time.time()
    last_autosave_time = time.time()
    autosave_interval = getattr(cfg, 'AUTOSAVE_INTERVAL_SEC', 1800.0)
    last_updates_count = updates_done
    start_time_total = time.time()
    last_steps_ingested = total_steps_ingested

    hyperparameters = {k: v for k, v in vars(cfg).items() if not k.startswith('_')}

    try:
        while not should_stop():
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
                    break

            if exp_queue.empty() and not any(p.is_alive() for p in actor_processes):
                print("\n[Learner] All actors have finished their episodes and queue is drained. Finishing training...")
                break

            if len(memory) >= cfg.MIN_BUFFER_SIZE:
                transitions = memory.sample(cfg.BATCH_SIZE)
                batch_state, batch_action, batch_reward, batch_next_state, batch_done = zip(*transitions)

                max_nodes = max(state[0].shape[0] for state in batch_state)
                max_edges = max(state[1].shape[1] for state in batch_state)
                max_next_nodes = max(n_state[0].shape[0] for n_state in batch_next_state)
                max_next_edges = max(n_state[1].shape[1] for n_state in batch_next_state)
                feature_dim = batch_state[0][0].shape[1]

                batched_s_nodes = torch.zeros((cfg.BATCH_SIZE, max_nodes, feature_dim), device=device)
                batched_s_H = torch.zeros((cfg.BATCH_SIZE, max_nodes, max_edges), device=device)
                node_masks = torch.zeros((cfg.BATCH_SIZE, max_nodes), dtype=torch.bool, device=device)

                batched_ns_nodes = torch.zeros((cfg.BATCH_SIZE, max_next_nodes, feature_dim), device=device)
                batched_ns_H = torch.zeros((cfg.BATCH_SIZE, max_next_nodes, max_next_edges), device=device)
                next_node_masks = torch.zeros((cfg.BATCH_SIZE, max_next_nodes), dtype=torch.bool, device=device)

                batched_h = torch.zeros((cfg.BATCH_SIZE, cfg.LSTM_HIDDEN_DIM), device=device)
                batched_c = torch.zeros((cfg.BATCH_SIZE, cfg.LSTM_HIDDEN_DIM), device=device)
                batched_nh = torch.zeros((cfg.BATCH_SIZE, cfg.LSTM_HIDDEN_DIM), device=device)
                batched_nc = torch.zeros((cfg.BATCH_SIZE, cfg.LSTM_HIDDEN_DIM), device=device)

                for i in range(cfg.BATCH_SIZE):
                    s_nodes, s_H = batch_state[i][0], batch_state[i][1]
                    n_nodes, n_edges = s_H.shape
                    batched_s_nodes[i, :n_nodes, :] = s_nodes.to(device)
                    batched_s_H[i, :n_nodes, :n_edges] = s_H.to(device)
                    node_masks[i, :n_nodes] = True

                    ns_nodes, ns_H = batch_next_state[i][0], batch_next_state[i][1]
                    nn_nodes, nn_edges = ns_H.shape
                    batched_ns_nodes[i, :nn_nodes, :] = ns_nodes.to(device)
                    batched_ns_H[i, :nn_nodes, :nn_edges] = ns_H.to(device)
                    next_node_masks[i, :nn_nodes] = True

                    # Load stored recurrent states (backwards-compatible with old 2-tuple checkpoints)
                    if len(batch_state[i]) == 3:
                        batched_h[i] = batch_state[i][2][0].squeeze(0).to(device)
                        batched_c[i] = batch_state[i][2][1].squeeze(0).to(device)
                        batched_nh[i] = batch_next_state[i][2][0].squeeze(0).to(device)
                        batched_nc[i] = batch_next_state[i][2][1].squeeze(0).to(device)

                batch_arange = torch.arange(cfg.BATCH_SIZE, device=device)

                # Forward pass with stored LSTM hidden states
                q_act_v, q_item_v, q_rot_v, q_map_v, _ = policy_net(
                    batched_s_nodes, batched_s_H, (batched_h, batched_c), mask=node_masks
                )

                # Double DQN Target Calculation
                with torch.no_grad():
                    # 1. Online policy_net selects greedy next actions
                    p_nq_act, p_nq_item, p_nq_rot, p_nq_map, _ = policy_net(
                        batched_ns_nodes, batched_ns_H, (batched_nh, batched_nc), mask=next_node_masks
                    )
                    next_act_idx = p_nq_act.argmax(dim=1)
                    next_item_idx = p_nq_item.argmax(dim=1)
                    next_rot_idx = p_nq_rot.argmax(dim=1)
                    next_map_idx = p_nq_map.view(cfg.BATCH_SIZE, -1).argmax(dim=1)

                    # 2. Target network evaluates the actions selected by policy_net
                    nq_act, nq_item, nq_rot, nq_map, _ = target_net(
                        batched_ns_nodes, batched_ns_H, (batched_nh, batched_nc), mask=next_node_masks
                    )

                    next_uses_item = ((next_act_idx == 2) | (next_act_idx == 3) | (next_act_idx == 4) | (next_act_idx == 6)).float()
                    next_uses_rot = (next_act_idx == 3).float()
                    next_uses_map = (next_act_idx != 2).float()

                    max_nq_act = nq_act[batch_arange, next_act_idx]
                    max_nq_item = nq_item[batch_arange, next_item_idx] * next_uses_item
                    max_nq_rot = nq_rot[batch_arange, next_rot_idx] * next_uses_rot
                    max_nq_map = nq_map.view(cfg.BATCH_SIZE, -1)[batch_arange, next_map_idx] * next_uses_map

                    active_heads = 1.0 + next_uses_item + next_uses_rot + next_uses_map
                    max_q = (max_nq_act + max_nq_item + max_nq_rot + max_nq_map) / active_heads

                    r_tensor = torch.tensor(batch_reward, dtype=torch.float32, device=device)
                    d_tensor = torch.tensor(batch_done, dtype=torch.float32, device=device)
                    target_vals = r_tensor + cfg.GAMMA * max_q * (1.0 - d_tensor)

                actions_t = torch.tensor(batch_action, dtype=torch.long, device=device)
                act_idx, item_idx, rot_idx, map_idx = actions_t[:, 0], actions_t[:, 1], actions_t[:, 2], actions_t[:, 3]

                chosen_q_act = q_act_v[batch_arange, act_idx]
                chosen_q_item = q_item_v[batch_arange, item_idx]
                chosen_q_rot = q_rot_v[batch_arange, rot_idx]
                chosen_q_map = q_map_v.view(cfg.BATCH_SIZE, -1)[batch_arange, map_idx]

                uses_item = ((act_idx == 2) | (act_idx == 3) | (act_idx == 4) | (act_idx == 6)).float()
                uses_rot = (act_idx == 3).float()
                uses_map = (act_idx != 2).float()

                loss_act = nn.functional.smooth_l1_loss(chosen_q_act, target_vals)
                loss_item = (nn.functional.smooth_l1_loss(chosen_q_item, target_vals, reduction='none') * uses_item).mean()
                loss_rot = (nn.functional.smooth_l1_loss(chosen_q_rot, target_vals, reduction='none') * uses_rot).mean()
                loss_map = (nn.functional.smooth_l1_loss(chosen_q_map, target_vals, reduction='none') * uses_map).mean()

                loss = loss_act + loss_item + loss_rot + loss_map

                optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(policy_net.parameters(), max_norm=1.0)
                optimizer.step()

                updates_done += 1
                current_loss = loss.item()

                if updates_done % cfg.TARGET_UPDATE == 0:
                    target_net.load_state_dict(policy_net.state_dict())
                    shared_policy.load_state_dict({k: v.cpu() for k, v in policy_net.state_dict().items()})
                    print(f"[Learner] Target updated & weights synced to CPU at {updates_done} updates. Loss: {current_loss:.4f}")

                    current_time = time.time()
                    if current_time - last_json_update > cfg.UPDATE_INTERVAL_SEC:
                        elapsed_interval = current_time - last_json_update
                        elapsed_tot = current_time - start_time_total

                        updates_in_interval = updates_done - last_updates_count
                        updates_per_sec = updates_in_interval / elapsed_interval

                        steps_in_interval = total_steps_ingested - last_steps_ingested
                        ingestion_rate = steps_in_interval / elapsed_interval

                        training_rate = updates_per_sec * cfg.BATCH_SIZE
                        utd_ratio = training_rate / ingestion_rate if ingestion_rate > 0 else 0.0

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

                if time.time() - last_autosave_time >= autosave_interval:
                    save_checkpoint(
                        cfg.AUTOSAVE_PATH, policy_net, target_net, optimizer,
                        memory, total_steps_ingested, updates_done, cfg
                    )
                    last_autosave_time = time.time()
            else:
                time.sleep(0.05)

    finally:
        if updates_done > 0:
            print("\n[Learner] Shutting down — saving final rolling checkpoint and weights...")
            save_checkpoint(
                cfg.AUTOSAVE_PATH, policy_net, target_net, optimizer,
                memory, total_steps_ingested, updates_done, cfg
            )


# this line should make sure that any not implemented MPS operations will throw CPU fallback errors instead of crashing the process
# this should make it carry on the operation on the cpu
# since i dont know what specific operation might happen and cant fix a not implemented error cus im NOT like that
# we just use this line instead
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

def main():
    mp.set_start_method('spawn', force=True)

    global cfg
    cfg = Config()  # Reload fresh config from user_config.json
    os.makedirs(cfg.SAVE_FOLDER, exist_ok=True)

    if os.path.exists(STOP_TRAIN_FILE):
        try:
            os.remove(STOP_TRAIN_FILE)
        except OSError:
            pass

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
        learner_loop(shared_policy_net, experience_queue, gpu_device, cfg, actor_processes)
        print("[Master] Learner finished.")
    except KeyboardInterrupt:
        print("\n[Master] Ctrl+C detected. Signaling Actors to pack up and delete their containers...")
        with open(STOP_TRAIN_FILE, "w") as f:
            f.write("stop")
    finally:
        print("[Master] Waiting for Actor processes to clean up containers...")
        for p in actor_processes:
            p.join(timeout=15)

        # If any actor is totally frozen and didn't shut down after 15 seconds, force terminate
        for p in actor_processes:
            if p.is_alive():
                print(f"[Master] Force terminating stuck process: {p.name}")
                p.terminate()

        if os.path.exists(STOP_TRAIN_FILE):
            try:
                os.remove(STOP_TRAIN_FILE)
            except OSError:
                pass
        print("[Master] All containers deleted. Shutdown complete.")

if __name__ == '__main__':
    main()