import shutil
import time
import torch
import torch.nn as nn
import numpy as np
import random
from collections import deque, defaultdict
from tqdm import tqdm
import os
import traceback
import json
import docker
import timeit

from OrePatchDetector import OrePatchDetector
from config import Config
from environment import FactorioEnv
from FactorioHGNN import FactorioHGNN
from mappings import get_available_items
from rcon_bridge_1_0_0.rcon_bridge import Rcon_reciever
from ActionMasking import get_action_masks

# --- Parameters ---
WEIGHTS_PATH = "jimbo_dqn_weights.pth"  # Path to trained model
CONTAINER_NAME = "factorio"
SAVE_FOLDER = r"C:\factorio_data\saves"
SAVES_POOL = "./SAVES_POOL"
epsilon_inference = 0.02  # Very low noise to prevent getting stuck in infinite loops


class MapScheduler:
    def __init__(self, pool_path):
        self.pool_path = pool_path
        self.queue = []

    def get_next_map(self):
        if not self.queue:
            print("Map queue empty. Refilling and shuffling...")
            self.queue = [f for f in os.listdir(self.pool_path) if f.endswith('.zip')]
            random.shuffle(self.queue)
        return self.queue.pop()


def apply_mask_to_logits(logits, mask):
    """Sets logits to -inf where mask is 0."""
    if not isinstance(mask, torch.Tensor):
        mask_t = torch.tensor(mask, device=logits.device, dtype=torch.bool)
    else:
        mask_t = mask.bool()

    masked_logits = logits.clone()
    masked_logits[~mask_t] = -1e9
    return masked_logits


def select_action(model, node_feats, H, hidden_state, epsilon, device, masks):
    """
    Identical to training logic, but allows us to force low/zero epsilon.
    """
    act_mask, item_mask, space_mask = masks

    # Even in inference, a tiny bit of epsilon helps break "wiggling" loops
    if random.random() < epsilon:
        # --- MASKED RANDOM ---
        valid_actions = np.nonzero(act_mask)[0]
        act = random.choice(valid_actions) if len(valid_actions) > 0 else 0

        valid_items = np.nonzero(item_mask[act])[0]
        item = random.choice(valid_items) if len(valid_items) > 0 else 0

        rot = random.randint(0, 3)

        valid_locs = np.nonzero(space_mask[act])[0]
        heatmap_idx = random.choice(valid_locs) if len(valid_locs) > 0 else 0

        h_next = (torch.zeros(1, 256).to(device), torch.zeros(1, 256).to(device))
        return act, item, rot, heatmap_idx, h_next

    else:
        # --- MASKED GREEDY ---
        with torch.no_grad():
            q_act, q_item, q_rot, q_map, h_next = model(node_feats, H, hidden_state)

            # 1. Mask Action
            masked_q_act = apply_mask_to_logits(q_act.view(-1), act_mask)
            act = masked_q_act.argmax().item()

            # 2. Mask Item (dependent on action)
            masked_q_item = apply_mask_to_logits(q_item.view(-1), item_mask[act])
            item = masked_q_item.argmax().item()

            # 3. Rotation
            rot = q_rot.argmax().item()

            # 4. Mask Heatmap (dependent on action)
            masked_q_map = apply_mask_to_logits(q_map.view(-1), space_mask[act])
            heatmap_idx = masked_q_map.argmax().item()

            return act, item, rot, heatmap_idx, h_next


def play():
    cfg = Config()
    # Force verbose to true to see what the bot is doing
    Config.VERBOSE = True

    env = FactorioEnv(cfg)

    # 1. Device Setup
    if torch.backends.mps.is_available():
        device = torch.device("mps")
    elif torch.cuda.is_available():
        device = torch.device("cuda")
    else:
        device = torch.device("cpu")
    print(f"Inference running on {device}")

    # 2. Load Model
    model = FactorioHGNN(hidden_dim=cfg.HIDDEN_DIM, lstm_hidden_dim=cfg.LSTM_HIDDEN_DIM).to(device)

    if os.path.exists(WEIGHTS_PATH):
        print(f"Loading weights from {WEIGHTS_PATH}...")
        # map_location ensures weights load to the correct device
        model.load_state_dict(torch.load(WEIGHTS_PATH, map_location=device, weights_only=True))
    else:
        print(f"CRITICAL: Weights file {WEIGHTS_PATH} not found!")
        return

    model.eval()

    # 3. Map Scheduler
    map_scheduler = MapScheduler(SAVES_POOL)

    print("\n=== STARTING INFINITE PLAY LOOP ===")
    print("Press Ctrl+C to stop.")

    while True:
        # --- PREPARATION PHASE (Docker & Maps) ---
        try:
            # Pick Map
            TARGET_SAVE = map_scheduler.get_next_map()
            print(f"\nLoading Map: {TARGET_SAVE}")

            # Docker Reset
            docker_client = docker.from_env()
            container = docker_client.containers.get(CONTAINER_NAME)

            print(f"Resetting environment...")
            container.stop()
            time.sleep(2)

            # Clean saves
            for item in os.listdir(SAVE_FOLDER):
                item_path = os.path.join(SAVE_FOLDER, item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)

            # Copy new save
            shutil.copy2(os.path.join(SAVES_POOL, TARGET_SAVE), os.path.join(SAVE_FOLDER, TARGET_SAVE))

            container.start()
            print("Server starting...")
            time.sleep(10)  # Wait for boot

            # Ore Scanning (Crucial for ActionMasking)
            receiver_ore = Rcon_reciever("localhost", "eenie7Uphohpaim", 27015)
            ore_map = receiver_ore.scan_ore()
            time.sleep(2)

            detector = OrePatchDetector(ore_map)
            patches = detector.process_patches()
            receiver_ore.disconnect()
            print(f"Ores detected: {len(patches)} patches found.")

        except Exception as e:
            print(f"Error during setup: {e}")
            time.sleep(5)
            continue

        # --- GAMEPLAY PHASE ---
        obs = env.reset()
        if obs is None: continue

        # Reset Hidden State
        hidden_state = (torch.zeros(1, cfg.LSTM_HIDDEN_DIM).to(device),
                        torch.zeros(1, cfg.LSTM_HIDDEN_DIM).to(device))

        total_reward = 0

        # We use a progress bar to show steps, but we don't really care about 'training' speed
        with tqdm(range(cfg.MAX_TIMESTEPS), desc=f"Playing {TARGET_SAVE}", unit="step") as pbar:
            for t in pbar:
                # 1. Get Obs
                if t > 0:
                    obs = env.get_observation()

                node_feats, H = obs
                node_feats = node_feats.to(device)
                H = H.to(device)

                # 2. Update Masks
                # This mirrors the training logic exactly to ensure the bot sees the world correctly
                raw_entities = env._last_raw_entities
                raw_player = env._last_raw_player
                inventory = {item.get('name'): item.get('count', 0) for item in raw_player.get('inventory', [])}
                bounds = env.current_bounds

                # Check research for available items
                research = env.receiver.scan_research()
                valid_items = get_available_items(research)

                masks = get_action_masks(
                    entities=raw_entities,
                    player_info=raw_player,
                    inventory=inventory,
                    available_items=valid_items,
                    bounds=bounds,
                    patches=patches,
                    move_state=env.move_state
                )

                # 3. Select Action
                act, item, rot, map_idx, next_hidden = select_action(
                    model, node_feats, H, hidden_state, epsilon_inference, device, masks
                )

                hidden_state = next_hidden

                # Convert Coords
                y_grid = map_idx // 17
                x_grid = map_idx % 17
                x_norm = -1.0 + (x_grid / 16.0) * 2.0
                y_norm = -1.0 + (y_grid / 16.0) * 2.0

                # 4. Step
                next_obs, reward, done, _ = env.step(act, item, rot, x_norm, y_norm)
                total_reward += reward

                pbar.set_postfix(Reward=f"{total_reward:.1f}", LastAct=act)

                if done:
                    print(f"\nEpisode finished. Total Reward: {total_reward}")
                    break

        env.close()
        print("Moving to next map...")


if __name__ == "__main__":
    try:
        play()
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Fatal Error: {e}")
        traceback.print_exc()