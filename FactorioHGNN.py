import math
import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import List, Dict, Any, Optional, Tuple

# Import mappings to get category sizes
from mappings import (
    MACHINE_NAME_MAP,
    STATUS_MAP,
    MINING_TARGET_MAP,
    RECIPE_MAP,
    ITEM_MAP, ACTION_MAP
)

# --- Category Size Definitions ---
N_MACHINE_TYPES = max(MACHINE_NAME_MAP.values()) + 1
N_STATUS_TYPES = max(STATUS_MAP.values()) + 1
N_MINING_TARGETS = max(MINING_TARGET_MAP.values()) + 1
N_RECIPES = max(RECIPE_MAP.values()) + 1
N_ITEM_TYPES = max(ITEM_MAP.values()) + 1
N_ACTIONS = max(ACTION_MAP.values()) + 1
N_ROTATIONS = 4 + 1

# --- Feature Dimension ---
N_CONTINUOUS_FEATURES = 5
FEATURE_DIM = (
        N_CONTINUOUS_FEATURES +
        N_MACHINE_TYPES +
        N_STATUS_TYPES +
        N_MINING_TARGETS +
        N_RECIPES +
        N_ITEM_TYPES +
        N_ROTATIONS
)


def create_grid_hypergraph(entities: List[Any], grid_size: int = 10) -> torch.Tensor:
    """
    Creates a hypergraph incidence matrix based on a spatial grid.
    Returns H: (num_nodes, num_hyperedges)
    """
    grid: Dict[tuple, list] = {}

    for i, e in enumerate(entities):
        # Ensure we access attributes correctly whether entity is dict or object
        x = e.x if hasattr(e, 'x') else e.get('x', 0)
        y = e.y if hasattr(e, 'y') else e.get('y', 0)

        cell_x = int(x) // grid_size
        cell_y = int(y) // grid_size
        cell_id = (cell_x, cell_y)

        if cell_id not in grid:
            grid[cell_id] = []
        grid[cell_id].append(i)

    num_nodes = len(entities)
    num_hyperedges = len(grid)

    if num_nodes == 0 or num_hyperedges == 0:
        return torch.zeros((num_nodes, max(1, num_hyperedges)))

    cell_to_edge_id = {cell_id: i for i, cell_id in enumerate(grid.keys())}
    H = torch.zeros((num_nodes, num_hyperedges))

    for cell_id, node_indices in grid.items():
        edge_id = cell_to_edge_id[cell_id]
        H[node_indices, edge_id] = 1.0

    return H

def create_functional_hypergraph(feature_list: List[Dict[str, Any]],
                                 edges: List[Dict[str, Any]],
                                 total_nodes: int) -> torch.Tensor:
    """
    Creates an incidence matrix H based on functional connections.
    Updated to accept total_nodes to avoid post-hoc padding.
    """
    num_edges = len(edges)

    # Initialize Incidence Matrix with the CORRECT full size immediately
    # Shape: (Total Nodes including Player, Edges)
    H = torch.zeros((total_nodes, max(1, num_edges)))

    if num_edges == 0:
        return H

    # 1. Build Coordinate Mapping: (x, y) -> Node Index
    coord_to_idx = {}
    for i, feat in enumerate(feature_list):
        x = feat.get('x') if isinstance(feat, dict) else feat.x
        y = feat.get('y') if isinstance(feat, dict) else feat.y
        coord_to_idx[(x, y)] = i

    # 2. Populate Matrix
    for i, edge in enumerate(edges):
        src_key = (edge['from_x'], edge['from_y'])
        dst_key = (edge['to_x'], edge['to_y'])

        u = coord_to_idx.get(src_key)
        v = coord_to_idx.get(dst_key)

        if u is not None and v is not None:
            H[u, i] = 1.0
            H[v, i] = 1.0

    return H


def preprocess_features_for_gnn(feature_list: List[Dict[str, Any]],
                                player_info: Optional[Dict[str, Any]] = None) -> torch.Tensor:
    """
    Transforms feature dicts into a 2D tensor.
    Implements Point 3: Better defaults and scaling.
    """
    num_entities = len(feature_list)
    total_nodes = num_entities + (1 if player_info else 0)
    output_tensor = torch.zeros((total_nodes, FEATURE_DIM))

    for i, features in enumerate(feature_list):
        # Continuous
        output_tensor[i, 0] = features.get('x') or 0.0
        output_tensor[i, 1] = features.get('y') or 0.0
        output_tensor[i, 2] = float(features.get('energy') or 0.0)
        output_tensor[i, 3] = float(features.get('is_crafting') or 0.0)
        # Point 3: Changed to Log10 for better scaling
        output_tensor[i, 4] = math.log10(1.0 + float(features.get('products_finished') or 0.0))

        # One-Hot Encoding - Point 3: Use last index as default "N/A"
        current_idx = N_CONTINUOUS_FEATURES

        # Machine
        machine_val = features.get('machine', N_MACHINE_TYPES - 1)
        output_tensor[i, current_idx + machine_val] = 1.0
        current_idx += N_MACHINE_TYPES

        # Status
        status_val = features.get('status')
        if status_val is None:
            status_val = N_STATUS_TYPES - 1
        output_tensor[i, current_idx + status_val] = 1.0
        current_idx += N_STATUS_TYPES
        # Mining Target
        mining_val = features.get('mining_target')
        if mining_val is None:
            mining_val = N_MINING_TARGETS - 1
        output_tensor[i, current_idx + mining_val] = 1.0
        current_idx += N_MINING_TARGETS
        # Recipe
        recipe_val = features.get('recipe')
        if recipe_val is None:
            recipe_val = N_RECIPES - 1


        output_tensor[i, current_idx + recipe_val] = 1.0

        current_idx += N_RECIPES

        # Items (skipped for machines)
        current_idx += N_ITEM_TYPES

        # Rotation
        rotation_val = features.get('rotation')
        rot_idx = (rotation_val + 1) if rotation_val is not None else 0
        output_tensor[i, current_idx + rot_idx] = 1.0
    # Player Node - Explicitly Inserted
    if player_info:
        p_idx = num_entities
        output_tensor[p_idx, 0] = player_info.get('x', 0.0)
        output_tensor[p_idx, 1] = player_info.get('y', 0.0)

        # Calculate start index for Items
        item_start_idx = (N_CONTINUOUS_FEATURES +
                          N_MACHINE_TYPES +
                          N_STATUS_TYPES +
                          N_MINING_TARGETS +
                          N_RECIPES)

        inventory = player_info.get('inventory', {})
        for item_id, count in inventory.items():
            if 0 < item_id < N_ITEM_TYPES:
                # Log scale inventory too for consistency
                output_tensor[p_idx, item_start_idx + item_id] = math.log10(1.0 + float(count))

    return output_tensor


class HypergraphConv(nn.Module):
    """
    Hypergraph convolution layer.
    Point 1: Updated with robust normalization D_v^-1 * H * D_e^-1 * H^T
    """

    def __init__(self, in_features, out_features):
        super(HypergraphConv, self).__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.weight = nn.Parameter(torch.FloatTensor(in_features, out_features))
        nn.init.xavier_uniform_(self.weight)

    def forward(self, x, H):
        if H.dim() == 2:
            # Single instance case
            N, E = H.shape
            if E == 0:
                return torch.zeros((N, self.out_features), device=x.device)

            # 1. Edge Degree D_e
            d_e = H.sum(dim=0)
            d_e_inv = torch.pow(d_e + 1e-6, -1.0)
            D_e_inv = torch.diag(d_e_inv)

            # 2. Node Degree D_v (Sum of rows of H)
            d_v = H.sum(dim=1)
            d_v_inv = torch.pow(d_v + 1e-6, -1.0)
            D_v_inv = torch.diag(d_v_inv)

            # 3. Adjacency with Normalization
            # A = D_v_inv @ H @ D_e_inv @ H.T
            H_T = H.transpose(0, 1)
            A = D_v_inv @ H @ D_e_inv @ H_T

            # 4. Propagation
            output = A @ x @ self.weight
            return output

        elif H.dim() == 3:
            # Batched case
            B, N, E = H.shape
            if E == 0:
                return torch.zeros((B, N, self.out_features), device=x.device)

            # 1. Edge Degree
            d_e = H.sum(dim=1)
            d_e_inv = torch.pow(d_e + 1e-6, -1.0)
            D_e_inv = torch.diag_embed(d_e_inv)

            # 2. Node Degree
            d_v = H.sum(dim=2)  # Sum across edges for each node
            d_v_inv = torch.pow(d_v + 1e-6, -1.0)
            D_v_inv = torch.diag_embed(d_v_inv)

            # 3. Adjacency
            H_T = H.transpose(1, 2)
            # A = D_v_inv @ H @ D_e_inv @ H_T
            term1 = torch.bmm(D_v_inv, H)
            term2 = torch.bmm(term1, D_e_inv)
            A = torch.bmm(term2, H_T)

            # 4. Propagation
            x_w = x @ self.weight
            output = torch.bmm(A, x_w)
            return output
        else:
            raise ValueError("Incidence matrix H must be 2D or 3D.")


# (Rest of FactorioHGNN class remains largely the same, logic is inside Convolution)
class GlobalAttention(nn.Module):
    def __init__(self, in_features):
        super(GlobalAttention, self).__init__()
        self.attn_gate = nn.Linear(in_features, in_features)
        self.attn_score = nn.Linear(in_features, 1)

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        is_batched = x.dim() == 3
        if not is_batched:
            if x.shape[0] == 0:
                return torch.zeros(self.attn_gate.in_features, device=x.device)
            x = x.unsqueeze(0)

        z = torch.tanh(self.attn_gate(x))
        scores = self.attn_score(z)

        if mask is not None:
            mask_expanded = mask.unsqueeze(-1)
            scores = scores.masked_fill(~mask_expanded, float('-inf'))

        weights = F.softmax(scores, dim=1)
        g = torch.sum(weights * x, dim=1)

        if not is_batched:
            return g.squeeze(0)
        return g


class FactorioHGNN(nn.Module):
    def __init__(self,
                 in_features: int = FEATURE_DIM,
                 hidden_dim: int = 256,
                 lstm_hidden_dim: int = 256,
                 n_actions: int = N_ACTIONS,
                 n_items: int = N_RECIPES
                 ):
        super(FactorioHGNN, self).__init__()

        self.in_features = in_features
        self.hidden_dim = hidden_dim
        self.lstm_hidden_dim = lstm_hidden_dim
        self.n_actions = n_actions
        self.n_items = n_items

        self.hgc1 = HypergraphConv(in_features, hidden_dim)
        self.hgc2 = HypergraphConv(hidden_dim, hidden_dim)
        self.relu = nn.ReLU()

        self.attention_pool = GlobalAttention(hidden_dim)
        self.lstm = nn.LSTMCell(input_size=hidden_dim, hidden_size=lstm_hidden_dim)

        self.action_head = nn.Sequential(
            nn.Linear(lstm_hidden_dim, lstm_hidden_dim // 2), nn.ReLU(),
            nn.Linear(lstm_hidden_dim // 2, n_actions)
        )
        self.item_head = nn.Sequential(
            nn.Linear(lstm_hidden_dim, lstm_hidden_dim // 2), nn.ReLU(),
            nn.Linear(lstm_hidden_dim // 2, n_items)
        )
        self.heatmap_head = nn.Sequential(
            nn.Linear(lstm_hidden_dim, lstm_hidden_dim), nn.ReLU(),
            nn.Linear(lstm_hidden_dim, 17 * 17)
        )
        self.rotation_head = nn.Sequential(
            nn.Linear(lstm_hidden_dim, lstm_hidden_dim // 2), nn.ReLU(),
            nn.Linear(lstm_hidden_dim // 2, 4)
        )

    def forward(self, x, H, hidden_state=None, mask=None):
        batch_size = x.shape[0] if x.dim() == 3 else 1
        device = x.device

        if hidden_state is None:
            h_0 = torch.zeros(batch_size, self.lstm_hidden_dim, device=device)
            c_0 = torch.zeros(batch_size, self.lstm_hidden_dim, device=device)
            hidden_state = (h_0, c_0)

        if x.dim() == 2 and x.shape[0] == 0:
            g = torch.zeros(batch_size, self.hidden_dim, device=device)
        else:
            x_emb = self.relu(self.hgc1(x, H))
            x_emb = self.relu(self.hgc2(x_emb, H))
            g = self.attention_pool(x_emb, mask=mask)
            if g.dim() == 1: g = g.unsqueeze(0)

        h_n, c_n = self.lstm(g, hidden_state)
        next_hidden_state = (h_n, c_n)

        action_logits = self.action_head(h_n)
        item_logits = self.item_head(h_n)
        rotation_logits = self.rotation_head(h_n)
        heatmap_logits = self.heatmap_head(h_n).view(batch_size, 17, 17)

        if batch_size == 1:
            heatmap_logits = heatmap_logits.squeeze(0)

        return action_logits, item_logits, rotation_logits, heatmap_logits, next_hidden_state