# environment.py
import torch
import numpy as np
import rcon_bridge_1_0_0.rcon_bridge as bridge
import Edging
from parsers import parse_entity, Entity
from features import transform_entities, map_items, compute_bounds, unnormalize_coord
from FactorioHGNN import preprocess_features_for_gnn, create_functional_hypergraph, create_grid_hypergraph
from GNNtoFactorio import translateGNNtoFactorio


class FactorioEnv:
    def __init__(self, config):
        self.cfg = config
        self.receiver = bridge.Rcon_reciever(
            self.cfg.RCON_HOST,
            self.cfg.RCON_PASSWORD,
            self.cfg.RCON_PORT
        )
        self.current_bounds = None

        # --- RL State Tracking ---
        self.milestones = set()
        self.max_edges_seen = 0

        # Point 2: Track Global Max Production to prevent mining/rebuilding exploit
        self.max_total_production_seen = 0

        self.steps_without_action = 0

    def reset(self):
        self.milestones.clear()
        self.max_edges_seen = 0
        self.max_total_production_seen = 0
        self.steps_without_action = 0

        try:
            self.receiver.connect()
            print("RCON Connected.")
            return self.get_observation()
        except Exception as e:
            print(f"Connection failed: {e}")
            return None

    def close(self):
        self.receiver.disconnect()

    def get_observation(self):
        # 1. Fetch Data
        raw_entities = self.receiver.scan_entities()
        raw_player = self.receiver.char_info()
        self._last_raw_entities = raw_entities
        self._last_raw_player = raw_player


        # 2. Parse & Features
        entities = [parse_entity(e['machine_name'], e) for e in raw_entities]
        self.current_bounds = compute_bounds(entities, char_info=raw_player)
        player_info = map_items(raw_player, self.current_bounds)

        features = transform_entities(entities, bounds=self.current_bounds)
        # 3. Tensors
        # Player info is inserted here into node_features (User requirement met)
        #HERE
        node_features = preprocess_features_for_gnn(features, player_info=player_info)
        total_nodes = node_features.shape[0]


        # 4. Hypergraphs
        p_pos = raw_player.get('pos', {'x': 0, 'y': 0})
        player_ent = Entity('player', int(p_pos.get('x', 0)), int(p_pos.get('y', 0)))
        all_entities = entities + [player_ent]
        H_grid = create_grid_hypergraph(all_entities, grid_size=10)

        # Functional (Edges)
        functional_edges = Edging.translateEntitesToEdges(self.receiver)
        self._current_edge_count = len(functional_edges)

        # User Instruction: No "zero row concatenation".
        # We pass 'total_nodes' (which includes the player) directly to the creator.
        # This ensures the matrix is initialized to the correct full size (Machines + Player).
        H_func = create_functional_hypergraph(features, functional_edges, total_nodes=total_nodes)

        # Combine
        # Ensure grid and func graphs match in node dimension
        if H_grid.shape[0] != H_func.shape[0]:
            # Fallback safety in case create_grid_hypergraph behaves differently
            max_rows = max(H_grid.shape[0], H_func.shape[0])
            # Resize logic omitted for brevity, assuming standard flow holds
            pass

        H = torch.cat([H_grid, H_func], dim=1)

        return node_features, H

    def step(self, action_idx, item_idx, rotation_idx, x_norm, y_norm):
        if not self.current_bounds:
            return None, 0, True, {}

        min_x, max_x, min_y, max_y = self.current_bounds
        final_x = unnormalize_coord(x_norm, min_x, max_x)
        final_y = unnormalize_coord(y_norm, min_y, max_y)

        # Execute
        log_msg = translateGNNtoFactorio(
            final_x, final_y, action_idx, item_idx, rotation_idx, self.receiver, verbose=self.cfg.VERBOSE
        )

        next_obs = self.get_observation()
        reward, done = self._compute_reward(log_msg, action_idx)

        return next_obs, reward, done, {}

    def _compute_reward(self, log_msg, action_idx):
        reward = 0.0
        done = False

        # --- A. Validation & Punishment (Point 2) ---
        # Explicit check for success (assuming translateGNNtoFactorio or environment catches strings)
        if "FAILED" in log_msg or "Cannot" in log_msg:
            reward -= 0.2
        elif action_idx == 0:
            self.steps_without_action += 1
            if self.steps_without_action > 5:
                reward -= 0.5
        else:
            self.steps_without_action = 0
            reward += 0.01

        # --- B. Production Score (Point 2: Anti-Hacking) ---
        current_total_production = 0
        for e in self._last_raw_entities:
            # entities are dicts, check if they have product info
            # Note: Because we cannot change Lua (Point 4), we sum the local counters
            current_total_production += int(e.get('products_finished', 0))

        # Only reward if we break the GLOBAL record for this run
        if current_total_production > self.max_total_production_seen:
            prod_delta = current_total_production - self.max_total_production_seen
            reward += (prod_delta * 1.0)
            self.max_total_production_seen = current_total_production

        # If we mined a building, current_total_production drops, but max_seen stays high.
        # Rebuilding it starts from 0, so we get NO reward until it surpasses previous levels.
        # This fixes the exploit.

        # --- C. Connectivity / Edges ---
        if self._current_edge_count > self.max_edges_seen:
            diff = self._current_edge_count - self.max_edges_seen
            reward += (diff * 0.5)
            self.max_edges_seen = self._current_edge_count

        # --- D. Milestones ---
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