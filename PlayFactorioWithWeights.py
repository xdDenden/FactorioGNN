import shutil
import time
import torch
import torch.nn as nn
import numpy as np
import random
from collections import deque, defaultdict
from tqdm import tqdm
import os
import sys
from pathlib import Path
import traceback
import json
import docker
import timeit

from OrePatchDetector import OrePatchDetector
from RunConfig import Config
from environment import FactorioEnv
from FactorioHGNN import FactorioHGNN
from mappings import get_available_items
from rcon_bridge_1_0_0.rcon_bridge import Rcon_reciever
from ActionMasking import get_action_masks

"""
This is deprecated and outdated for the moment. Once this file gets brought inline with the others we will rewrite it.
Renaming from main to PlayFactorioWithWeights to actually reflect what this script is supposed to do.
"""

# 1. Define Defaults based on OS
if sys.platform.startswith("win"):
    base_save_path = Path(r"C:\factorio_data\saves")
else:
    # On Mac/Linux, use the user's home directory to avoid permission errors
    # Result: /Users/yourname/factorio_data/saves
    base_save_path = Path.home() / "factorio_data" / "saves"

# 2. Setup Paths (using pathlib for slash consistency)
WEIGHTS_PATH = Path("jimbo_dqn_weights.pth")
CONTAINER_NAME = "factorio"
SAVE_FOLDER = base_save_path
SAVES_POOL = Path("./SAVES_POOL").resolve() # .resolve() makes it absolute

epsilon_inference = 0.02

# 3. Sanity Checks
if not SAVE_FOLDER.exists():
    try:
        SAVE_FOLDER.mkdir(parents=True, exist_ok=True)
        print(f"Created missing save directory: {SAVE_FOLDER}")
    except PermissionError:
        print(f"CRITICAL: Cannot create {SAVE_FOLDER}. Check permissions or run with sudo.")
        sys.exit(1)

class MapScheduler:
    def __init__(self, pool_path):
        self.pool_path = Path(pool_path)
        self.queue = []

    def get_next_map(self):
        if not self.queue:
            print("Map queue empty. Refilling and shuffling...")
            # Use pathlib glob/iterdir
            self.queue = [f.name for f in self.pool_path.iterdir() if f.suffix == '.zip']
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
        # MASKED GREEDY
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
    print(f"Paths Configured -> Saves: {SAVE_FOLDER} | Pool: {SAVES_POOL}")

    # 2. Load Model
    model = FactorioHGNN(hidden_dim=cfg.HIDDEN_DIM, lstm_hidden_dim=cfg.LSTM_HIDDEN_DIM).to(device)

    if WEIGHTS_PATH.exists():
        print(f"Loading weights from {WEIGHTS_PATH}...")
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

            # Clean saves (Cross-platform way)
            # Iterate over the SAVE_FOLDER using pathlib
            for item in SAVE_FOLDER.iterdir():
                if item.is_file():
                    item.unlink() # Delete file
                elif item.is_dir():
                    shutil.rmtree(item) # Delete dir

            # Copy new save
            source_file = SAVES_POOL / TARGET_SAVE
            dest_file = SAVE_FOLDER / TARGET_SAVE
            shutil.copy2(source_file, dest_file)

            container.start()
            print("Server starting...")
            time.sleep(10)  # Wait for boot

            # Ore Scanning
            receiver_ore = Rcon_reciever("localhost", "eenie7Uphohpaim", w27015)
            ore_map = receiver_ore.scan_ore()
            time.sleep(2)

            detector = OrePatchDetector(ore_map)
            patches = detector.process_patches()
            receiver_ore.disconnect()
            print(f"Ores detected: {len(patches)} patches found.")

        except Exception as e:
            print(f"Error during setup: {e}")
            traceback.print_exc()
            time.sleep(5)
            continue

        # --- GAMEPLAY PHASE ---
        obs = env.reset()
        if obs is None: continue

        hidden_state = (torch.zeros(1, cfg.LSTM_HIDDEN_DIM).to(device),
                        torch.zeros(1, cfg.LSTM_HIDDEN_DIM).to(device))

        total_reward = 0

        with tqdm(range(cfg.MAX_TIMESTEPS), desc=f"Playing {TARGET_SAVE}", unit="step") as pbar:
            for t in pbar:
                if t > 0:
                    obs = env.get_observation()

                node_feats, H = obs
                node_feats = node_feats.to(device)
                H = H.to(device)

                # Update Masks
                raw_entities = env._last_raw_entities
                raw_player = env._last_raw_player
                inventory = {item.get('name'): item.get('count', 0) for item in raw_player.get('inventory', [])}
                bounds = env.current_bounds
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

                act, item, rot, map_idx, next_hidden = select_action(
                    model, node_feats, H, hidden_state, epsilon_inference, device, masks
                )

                hidden_state = next_hidden

                # Convert Coords
                y_grid = map_idx // 17
                x_grid = map_idx % 17
                x_norm = -1.0 + (x_grid / 16.0) * 2.0
                y_norm = -1.0 + (y_grid / 16.0) * 2.0

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