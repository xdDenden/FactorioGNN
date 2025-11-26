import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Any, Optional

# Import mappings to get category sizes
from mappings import (
    MACHINE_NAME_MAP,
    STATUS_MAP,
    MINING_TARGET_MAP,
    RECIPE_MAP,
    ITEM_MAP
)

# --- Category Size Definitions ---
# We add +1 to each to account for the '0' category, which we'll use for 'None' or 'Unknown'
N_MACHINE_TYPES = max(MACHINE_NAME_MAP.values()) + 1  # 0-34 -> 35 categories
N_STATUS_TYPES = max(STATUS_MAP.values()) + 1  # 0 (None) + 1-16 -> 17 categories
N_MINING_TARGETS = max(MINING_TARGET_MAP.values()) + 1  # 0 (None) + 1-4 -> 5 categories
N_RECIPES = max(RECIPE_MAP.values()) + 1  # 0 (None) + 1-52 -> 53 categories
N_ITEM_TYPES = max(ITEM_MAP.values()) + 1  # 0 (None) + 1-58 -> 59 categories
N_ACTIONS = max(STATUS_MAP.values()) + 1
N_ROTATIONS = 4 + 1  # 0 (None) + 0-3 (as 1-4) -> 5 categories


# --- Continuous & Boolean Feature Definitions ---
# x, y, energy, is_crafting, products_finished
N_CONTINUOUS_FEATURES = 5

# --- Total Feature Dimension ---
FEATURE_DIM = (
        N_CONTINUOUS_FEATURES +
        N_MACHINE_TYPES +
        N_STATUS_TYPES +
        N_MINING_TARGETS +
        N_RECIPES +
        N_ITEM_TYPES +
        N_ROTATIONS
)  # 5 + 35 + 17 + 5 + 59 + 5 + 53 = 179 dimensions


def preprocess_features_for_gnn(feature_list: List[Dict[str, Any]],
                                player_info: Optional[Dict[str, Any]] = None) -> torch.Tensor:
    """
    Transforms the list of feature dicts into a 2D tensor for the GNN.
    Handles one-hot encoding for categorical variables and imputes None values.

    Args:
        feature_list: List of dicts containing entity features.
        player_info: Optional dict containing processed player info ('x', 'y', 'inventory').
                     If provided, a row is added to the tensor for the player.
    """
    num_entities = len(feature_list)
    total_nodes = num_entities + (1 if player_info else 0)
    output_tensor = torch.zeros((total_nodes, FEATURE_DIM))

    # --- Process Standard Entities ---
    for i, features in enumerate(feature_list):
        # --- Continuous / Boolean Features (Indices 0-4) ---

        # x (normalized)
        output_tensor[i, 0] = features.get('x') or 0.0
        # y (normalized)
        output_tensor[i, 1] = features.get('y') or 0.0
        # energy (bool)
        output_tensor[i, 2] = float(features.get('energy') or 0.0)
        # is_crafting (bool)
        output_tensor[i, 3] = float(features.get('is_crafting') or 0.0)
        # products_finished (count) - using log(1+x) to stabilize
        output_tensor[i, 4] = math.log(1.0 + float(features.get('products_finished') or 0.0))

        # --- One-Hot Encoded Features ---
        current_idx = N_CONTINUOUS_FEATURES

        # Machine (35 categories, 0-34)
        machine_val = features.get('machine') or 0  # Default to 0
        output_tensor[i, current_idx + machine_val] = 1.0
        current_idx += N_MACHINE_TYPES

        # Status (17 categories, 0 for None, 1-16 for values)
        status_val = features.get('status') or 0  # 0 is 'None'
        output_tensor[i, current_idx + status_val] = 1.0
        current_idx += N_STATUS_TYPES

        # Mining Target (5 categories, 0 for None, 1-4 for values)
        mining_val = features.get('mining_target') or 0  # 0 is 'None'
        output_tensor[i, current_idx + mining_val] = 1.0
        current_idx += N_MINING_TARGETS

        # Recipe (53 categories, 0 for None, 1-52 for values)
        recipe_val = features.get('recipe') or 0  # 0 is 'None'
        output_tensor[i, current_idx + recipe_val] = 1.0
        current_idx += N_RECIPES

        # Item Types (59 categories)
        # Standard entities don't have explicit inventory mapped here in this version,
        # so we leave this section as zeros for machines.
        current_idx += N_ITEM_TYPES

        # Rotation (5 categories, 0 for None, 1-4 for values 0-3)
        rotation_val = features.get('rotation')
        if rotation_val is None:
            rot_idx = 0
        else:
            rot_idx = rotation_val + 1  # Map 0-3 to 1-4
        output_tensor[i, current_idx + rot_idx] = 1.0
        # current_idx += N_ROTATIONS # No need, it's the last one

    # --- Process Player Node (if provided) ---
    if player_info:
        p_idx = num_entities  # Player is the last node

        # 1. Continuous Features (x, y)
        output_tensor[p_idx, 0] = player_info.get('x', 0.0)
        output_tensor[p_idx, 1] = player_info.get('y', 0.0)
        # Energy, crafting, products -> 0

        # 2. Categorical Features
        # Machine, Status, Mining, Recipe -> 0 (None) for all
        # We need to find the start index for Items

        # Calculate start index for Items
        item_start_idx = (N_CONTINUOUS_FEATURES +
                          N_MACHINE_TYPES +
                          N_STATUS_TYPES +
                          N_MINING_TARGETS +
                          N_RECIPES)

        # 3. Inventory (encoded as sparse counts in the Item Types section)
        # player_info['inventory'] is { item_id: count }
        inventory = player_info.get('inventory', {})
        for item_id, count in inventory.items():
            if 0 < item_id < N_ITEM_TYPES:
                # We place the amount at the specific item index
                output_tensor[p_idx, item_start_idx + item_id] = float(count)

        # Rotation -> 0 (None) - Implicitly zero

    return output_tensor


def create_grid_hypergraph(entities: List[Any], grid_size: int = 10) -> torch.Tensor:
    """
    Creates a hypergraph incidence matrix based on a spatial grid.
    Each grid cell is a hyperedge, and nodes (entities) in that cell
    are part of that hyperedge.

    Args:
        entities: The *original* list of Entity objects (from parsers.py)
                  which contain the raw x, y coordinates.
        grid_size: The side length of each square grid cell.

    Returns:
        H: A (num_nodes, num_hyperedges) incidence matrix.
    """
    grid: Dict[tuple, list] = {}

    # 1. Assign nodes to grid cells
    for i, e in enumerate(entities):
        cell_x = int(e.x) // grid_size
        cell_y = int(e.y) // grid_size
        cell_id = (cell_x, cell_y)

        if cell_id not in grid:
            grid[cell_id] = []
        grid[cell_id].append(i)

    # 2. Build the incidence matrix H
    num_nodes = len(entities)
    num_hyperedges = len(grid)

    if num_nodes == 0 or num_hyperedges == 0:
        return torch.zeros((num_nodes, num_hyperedges))

    cell_to_edge_id = {cell_id: i for i, cell_id in enumerate(grid.keys())}
    H = torch.zeros((num_nodes, num_hyperedges))

    for cell_id, node_indices in grid.items():
        edge_id = cell_to_edge_id[cell_id]
        H[node_indices, edge_id] = 1.0

    return H


class HypergraphConv(nn.Module):
    """
    A simple hypergraph convolution layer based on the clique-expansion
    adjacency matrix: A = H * D_e^(-1) * H^T
    """

    def __init__(self, in_features, out_features):
        super(HypergraphConv, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.weight = nn.Parameter(torch.FloatTensor(in_features, out_features))
        nn.init.xavier_uniform_(self.weight)

    def forward(self, x, H):
        """
        Args:
            x (Tensor): Node features (N, F_in)
            H (Tensor): Incidence matrix (N, E)
        """
        N, E = H.shape
        if E == 0:  # Handle empty hypergraph
            return torch.zeros((N, self.out_features), device=x.device)

        # 1. Get hyperedge degrees (d_e)
        d_e = H.sum(dim=0)  # Shape (E,)

        # 2. Create inverse degree matrix D_e^(-1)
        # Add epsilon to avoid division by zero
        d_e_inv = torch.pow(d_e + 1e-6, -1.0)
        D_e_inv = torch.diag(d_e_inv)  # Shape (E, E)

        # 3. Transpose H
        H_T = H.transpose(0, 1)  # Shape (E, N)

        # 4. Compute clique-expansion adjacency matrix: A = H * D_e^(-1) * H^T
        A = H @ D_e_inv @ H_T  # Shape (N, N)

        # 5. Perform GCN-style propagation: A * X * W
        output = A @ x @ self.weight  # Shape (N, F_out)

        return output


class FactorioHGNN(nn.Module):
    """
    The main Hypergraph Neural Network model for Factorio.

    Takes node features and a hypergraph incidence matrix, and
    outputs logits for three distinct heads.
    """

    def __init__(self,
                 in_features: int = FEATURE_DIM,
                 hidden_dim: int = 256,
                 n_actions: int = N_ACTIONS,
                 n_items: int = N_RECIPES  # Use recipe list as item list
                 ):
        super(FactorioHGNN, self).__init__()

        self.in_features = in_features
        self.hidden_dim = hidden_dim
        self.n_actions = n_actions
        self.n_items = n_items

        # --- GNN Layers ---
        self.hgc1 = HypergraphConv(in_features, hidden_dim)
        self.hgc2 = HypergraphConv(hidden_dim, hidden_dim)
        self.relu = nn.ReLU()

        # --- Output Heads ---

        # Head 1: Action Selection (e.g., mine, craft, build, move)
        # Takes the global graph embedding and predicts an action
        self.action_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, n_actions)

        )


        # Head 2: Item Selection (e.g., copper-plate, iron-gear-wheel)
        # Takes the global graph embedding and predicts an item
        self.item_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, n_items)
        )

        # Head 3: Position Heatmap (17x17 grid)
        # Takes the global graph embedding and predicts a distribution
        # over a 17x17 grid relative to the player.
        self.heatmap_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, 17 * 17)
        )

        # Head 4: Rotation Selection (0-3)
        # Takes the global graph embedding and predicts a rotation
        self.rotation_head = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 4)  # 4 possible rotations
        )

    def forward(self, x: torch.Tensor, H: torch.Tensor):
        """
        Forward pass of the model.

        Args:
            x (Tensor): Node feature matrix (N, F_in)
            H (Tensor): Hypergraph incidence matrix (N, E)

        Returns:
            action_logits (Tensor): (n_actions,)
            item_logits (Tensor): (n_items,)
            heatmap_logits (Tensor): (17, 17)
        """
        if x.shape[0] == 0:  # Handle empty factory
            # Return zero logits for all heads
            action_logits = torch.zeros(self.n_actions, device=x.device)
            action_idx = action_logits.argmax().item()
            print(f"Predicted action index: {action_idx}")

            item_logits = torch.zeros(self.n_items, device=x.device)
            item_idx = action_logits.argmax().item()
            print(f"Predicted action index: {item_idx}")

            heatmap_logits = torch.zeros((17, 17), device=x.device)
            return action_logits, item_logits, heatmap_logits

        # 1. Pass through GNN layers
        x = self.relu(self.hgc1(x, H))
        x = self.relu(self.hgc2(x, H))  # Node embeddings (N, hidden_dim)

        # 2. Pool node features to get a global graph embedding
        # Using mean pooling here
        g = torch.mean(x, dim=0)  # Shape (hidden_dim,)

        # 3. Pass graph embedding through each head

        # --- Action Logits ---
        action_logits = self.action_head(g)
        action_idx = action_logits.argmax().item()
        print(f"Predicted action index: {action_idx}")

        # --- Item Logits ---
        item_logits = self.item_head(g)
        item_idx = item_logits.argmax().item()
        print(f"Predicted item index: {item_idx}")

        # --- Heatmap Logits ---
        heatmap_logits_flat = self.heatmap_head(g)
        heatmap_logits = heatmap_logits_flat.view(17, 17)

        # --- Rotation Logits ---
        rotation_logits = self.rotation_head(g)
        rotation_idx = rotation_logits.argmax().item()
        print(f"Predicted rotation index: {rotation_idx}")

        return action_logits, item_logits, heatmap_logits,action_idx,item_idx,rotation_idx