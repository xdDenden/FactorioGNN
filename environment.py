import json
import time
import torch
import numpy as np
import rcon_bridge.rcon_bridge as bridge
import Edging
import math
from parsers import parse_entity, Entity, parse_resource
from features import transform_entities, map_items, compute_bounds, unnormalize_coord
from FactorioHGNN import preprocess_features_for_gnn, create_functional_hypergraph, create_grid_hypergraph
from GNNtoFactorio import translateGNNtoFactorio
from ActionMasking import get_action_masks
from OrePatchDetector import OrePatchDetector


class PatchNode:
    """Helper class to represent an ore patch center as a graph node."""
    def __init__(self, ore_name, x, y):
        # type is set to something not in MACHINE_NAME_MAP so it maps to 0 (None)
        self.type = "resource-patch"
        self.x = x
        self.y = y
        # features.py looks for 'ore_name' to set the mining_target feature
        self.ore_name = ore_name


class FactorioEnv:
    def __init__(self, config, rcon_port=None, actor_id=0):
        self.cfg = config
        self.actor_id = actor_id

        # Use dynamic port if provided by the Actor, otherwise fallback to config
        active_port = rcon_port if rcon_port is not None else self.cfg.RCON_PORT

        self.receiver = bridge.Rcon_reciever(
            self.cfg.RCON_HOST,
            self.cfg.RCON_PASSWORD,
            active_port
        )
        self.current_bounds = None

        # RL State Tracking
        self.milestones = set()
        self.max_edges_seen = 0
        self.max_total_production_seen = 0
        self.successful_crafts = 0
         # Store patch nodes here so we don't re-calculate them every step
        self.patch_nodes = []
        self.steps_without_action = 0

        # Movement State Tracking
        self.move_state = {
            'active': False,
            'target': (0.0, 0.0),
            'timer': 0
        }

    def reset(self):
        self.milestones.clear()
        self.max_edges_seen = 0
        self.max_total_production_seen = 0
        self.successful_crafts = 0
        self.steps_without_action = 0
        self.patch_nodes = []

        # Reset Movement State
        self.move_state = {'active': False, 'target': (0.0, 0.0), 'timer': 0}

        try:
            self.receiver.connect()
            print("RCON Connected.")
            self.receiver.reset()
            time.sleep(5.0)  # Allow some time for the world to reset

            # 1. Scan Ores ONCE per episode
            raw_ores = self.receiver.scan_ore()

            time.sleep(2.0)
            # 2. Process into Patches (Midpoints)
            # This significantly reduces graph size (1000s of ore nodes -> ~10 patch nodes)
            if raw_ores:
                detector = OrePatchDetector(raw_ores)
                patches = detector.process_patches()

                for p in patches:
                    center = p['center']
                    # Create a virtual node for the graph
                    self.patch_nodes.append(
                        PatchNode(p['ore_type'], center[0], center[1])
                    )

                print(f"[actor {self.actor_id}] Processed {len(raw_ores)} ore entities into {len(self.patch_nodes)} patch centers.")
                self.current_patches = patches  # Store patches so the Actor can grab them for masking

            obs = self.get_observation()
            self._last_obs = obs
            return obs
        except Exception as e:
            print(f"Connection failed: {e}")
            return None

    def close(self):
        self.receiver.disconnect()

    def get_observation(self, scan_entities=True, char_info=True):
        # 1. Fetch Data
        if scan_entities:
            raw_entities = self.receiver.scan_entities()
            self._last_raw_entities = raw_entities
        else:
            raw_entities = self._last_raw_entities

        if char_info:
            raw_player = self.receiver.char_info()
            self._last_raw_player = raw_player
        else:
            raw_player = self._last_raw_player

        # 2. Parse & Features
        machine_entities = [parse_entity(e['machine_name'], e) for e in raw_entities]
        all_entities = machine_entities + self.patch_nodes

        self.current_bounds = compute_bounds(all_entities, char_info=raw_player)
        player_info = map_items(raw_player, self.current_bounds)

        features = transform_entities(all_entities, bounds=self.current_bounds)
        # 3. Tensors
        # Player info is inserted here into node_features
        node_features = preprocess_features_for_gnn(features, player_info=player_info)
        total_nodes = node_features.shape[0]


        # 4. Hypergraphs
        p_pos = raw_player.get('pos', {'x': 0, 'y': 0})
        player_ent = Entity('player', int(p_pos.get('x', 0)), int(p_pos.get('y', 0)))

        grid_entities = all_entities + [player_ent]
        H_grid = create_grid_hypergraph(grid_entities, grid_size=10)

        # Functional (Edges)
        # Note: Edges usually only exist between machines, not ore patches
        functional_edges = Edging.translateEntitesToEdges(self.receiver)
        self._current_edge_count = len(functional_edges)

        # No zero row concatenation (dont ask lol)
        # We pass 'total_nodes' (which includes the player) directly to the creator
        # This ensures the matrix is initialized to the correct full size (Machines + Player)
        H_func = create_functional_hypergraph(features, functional_edges, total_nodes=total_nodes)

        # Combine
        # Ensure grid and func graphs match in node dimension
        if H_grid.shape[0] != H_func.shape[0]:
             # This print helps debug if it happens again
             print(f"Shape Mismatch! Grid: {H_grid.shape}, Func: {H_func.shape}")
             # Force match if H_func is missing nodes (unlikely with fix above)
             if H_grid.shape[0] > H_func.shape[0]:
                 padding = torch.zeros((H_grid.shape[0] - H_func.shape[0], H_func.shape[1]))
                 H_func = torch.cat([H_func, padding], dim=0)

        H = torch.cat([H_grid, H_func], dim=1)

        return node_features, H

    def step(self, action_idx, item_idx, rotation_idx, x_norm, y_norm):
        if not self.current_bounds:
            return None, 0, True, {}
        min_x, max_x, min_y, max_y = self.current_bounds
        final_x = unnormalize_coord(x_norm, min_x, max_x)
        final_y = unnormalize_coord(y_norm, min_y, max_y)

        should_send_rcon = True
        log_msg = ""

        # 1. Action Logic
        if action_idx == 0:  # Action: MOVE_TO
            if self.move_state['active']:
                # IGNORE NEW MOVE COMMANDS while moving
                # We do NOT send RCON (prevents stuttering/spamming pathfinder)
                # We do NOT block the step (observation continues)
                should_send_rcon = False
                log_msg = "Move ignored (Already moving)"
            else:
                # Initiate NEW Move
                self.move_state['active'] = True
                self.move_state['target'] = (final_x, final_y)
                self.move_state['timer'] = 0
                should_send_rcon = True
                # Log message will be generated by translateGNNtoFactorio

        else:
            # Action: BUILD, CRAFT, MINE, ETC.
            # We ALWAYS execute these, even if moving.
            should_send_rcon = True

            # Note: We do NOT set move_state['active'] to False
            # The character will attempt to perform the action while walking
            # Factorio allows shooting/building while running

        # send rcon command if needed
        if should_send_rcon:
            log_msg = translateGNNtoFactorio(
                final_x, final_y, action_idx, item_idx, rotation_idx, self.receiver, verbose=self.cfg.VERBOSE
            )

        OBSERVE_ACTIONS = {1, 3, 6}
        if action_idx in OBSERVE_ACTIONS and "FAILED" not in log_msg:
            # Full Scan
            next_obs = self.get_observation(scan_entities=True, char_info=True)
            self._last_obs = next_obs
        elif action_idx == 0 and should_send_rcon:
            #We only do char_info
            next_obs = self.get_observation(scan_entities=False, char_info=True)
            self._last_obs = next_obs
        else:
            next_obs = self._last_obs

        # 3. Update Movement State (ALWAYS runs)
        # This tracks the movement initiated in previous steps, regardless of what we did this step
        if self.move_state['active']:
            self.move_state['timer'] += 1

            # Check Arrival
            px = self._last_raw_player.get('pos', {}).get('x', 0)
            py = self._last_raw_player.get('pos', {}).get('y', 0)
            tx, ty = self.move_state['target']
            dist = math.sqrt((px - tx)**2 + (py - ty)**2)

            if dist < 2.0 or self.move_state['timer'] >= 50:
                self.move_state['active'] = False
                # Optionally stop the character in game if they timed out?
                # self.receiver.send_command("/c game.player.walking_state = {walking=false}")
                # TODO: Check if this is necessary

        reward, done = self._compute_reward(log_msg, action_idx)

        return next_obs, reward, done, {}

    def _compute_reward(self, log_msg, action_idx):
        reward = 0.0
        done = False

        # Validation & Punishment
        if "FAILED" in log_msg or "Cannot" in log_msg:
            reward -= 0.2

        # Idle Punishment Logic
        is_doing_something_useful = False

        if action_idx != 0:
            is_doing_something_useful = True
        elif action_idx == 0 and self.move_state['active']:
            is_doing_something_useful = True

        if is_doing_something_useful:
            self.steps_without_action = 0
        else:
            self.steps_without_action += 1
            if self.steps_without_action > 5:
                reward -= 0.5

        # Crafting Reward (Modified with Hard Cap)
        if action_idx == 2:  # craft action
            # HARD CAP: 500 items.
            # After 500, the reward drops to 0, forcing the actor to Automate.
            if self.successful_crafts < 500:
                alpha = 0.1  # decay rate
                k = 5.0  # base reward
                reward += k / (1 + alpha * self.successful_crafts)
                self.successful_crafts += 1
            else:
                # Optional: You can add a small negative here if you want to
                # aggressively discourage hand-crafting late game, but 0 is usually safer
                pass

                # Production Score (prevent reward hacking by penalizing stagnant production)
                # TODO: check dynamic rewards on google docs
        current_total_production = 0
        for e in self._last_raw_entities:
            current_total_production += int(e.get('products_finished', 0))

        if current_total_production > self.max_total_production_seen:
            prod_delta = current_total_production - self.max_total_production_seen
            reward += (prod_delta * 1.0)
            self.max_total_production_seen = current_total_production

        # Connectivity / Edges
        alpha = 0.1
        k = 5.0
        if self._current_edge_count > self.max_edges_seen:
            diff = self._current_edge_count - self.max_edges_seen
            for i in range(diff):
                n = self.max_edges_seen + i
                reward += k / (1 + alpha * n)
            self.max_edges_seen = self._current_edge_count

        # Milestones
        # the agent gets a reward for achieving something for the first time
        # likely to be removed
        inv = self._last_raw_player.get("inventory", [])
        for item in inv:
            name = item.get("name", "unknown")
            count = item.get("count", 0)

            if name not in self.milestones:
                if "ore" in name:
                    reward += 5.0
                elif "plate" in name:
                    reward += 10.0
                elif "circuit" in name:
                    reward += 50.0
                else:
                    reward += 2.0
                self.milestones.add(name)

            if name == "advanced-circuit" and count >= 1:
                reward += 1000.0
                print("VICTORY: RED CIRCUIT PRODUCED!")
                done = True

        return reward, done
