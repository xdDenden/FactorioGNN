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
)


def preprocess_features_for_gnn(feature_list: List[Dict[str, Any]],
                                player_info: Optional[Dict[str, Any]] = None) -> torch.Tensor:
    """
    Transforms the list of feature dicts into a 2D tensor for the GNN.
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
        output_tensor[i, 4] = math.log(1.0 + float(features.get('products_finished') or 0.0))

        # One-Hot Encoding
        current_idx = N_CONTINUOUS_FEATURES

        # Machine
        machine_val = features.get('machine') or 0
        output_tensor[i, current_idx + machine_val] = 1.0
        current_idx += N_MACHINE_TYPES

        # Status
        status_val = features.get('status') or 0
        output_tensor[i, current_idx + status_val] = 1.0
        current_idx += N_STATUS_TYPES

        # Mining Target
        mining_val = features.get('mining_target') or 0
        output_tensor[i, current_idx + mining_val] = 1.0
        current_idx += N_MINING_TARGETS

        # Recipe
        recipe_val = features.get('recipe') or 0
        output_tensor[i, current_idx + recipe_val] = 1.0
        current_idx += N_RECIPES

        # Items (skipped for machines)
        current_idx += N_ITEM_TYPES

        # Rotation
        rotation_val = features.get('rotation')
        rot_idx = 0 if rotation_val is None else rotation_val + 1
        output_tensor[i, current_idx + rot_idx] = 1.0

    # Player Node
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
                output_tensor[p_idx, item_start_idx + item_id] = float(count)

    return output_tensor


def create_grid_hypergraph(entities: List[Any], grid_size: int = 10) -> torch.Tensor:
    """
    Creates a hypergraph incidence matrix based on a spatial grid.
    Returns H: (num_nodes, num_hyperedges)
    """
    grid: Dict[tuple, list] = {}

    for i, e in enumerate(entities):
        cell_x = int(e.x) // grid_size
        cell_y = int(e.y) // grid_size
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


class HypergraphConv(nn.Module):
    """
    Hypergraph convolution layer.
    A = H * D_e^(-1) * H^T
    Supports both 2D (Single) and 3D (Batched) inputs.
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
            x (Tensor): Node features (N, F_in) or (B, N, F_in)
            H (Tensor): Incidence matrix (N, E) or (B, N, E)
        """
        # Ensure H and x have compatible batch dimensions
        if H.dim() == 2:
            # Single instance case
            N, E = H.shape
            if E == 0:
                return torch.zeros((N, self.out_features), device=x.device)

            # 1. Degree
            d_e = H.sum(dim=0)
            d_e_inv = torch.pow(d_e + 1e-6, -1.0)
            D_e_inv = torch.diag(d_e_inv)

            # 2. Adjacency
            H_T = H.transpose(0, 1)
            A = H @ D_e_inv @ H_T

            # 3. Propagation
            output = A @ x @ self.weight
            return output

        elif H.dim() == 3:
            # Batched case (B, N, E)
            B, N, E = H.shape
            if E == 0:
                return torch.zeros((B, N, self.out_features), device=x.device)

            # 1. Degree (sum over nodes dim=1) -> (B, E)
            d_e = H.sum(dim=1)
            d_e_inv = torch.pow(d_e + 1e-6, -1.0)  # (B, E)
            D_e_inv = torch.diag_embed(d_e_inv)  # (B, E, E)

            # 2. Adjacency: H (B,N,E) @ D (B,E,E) @ H_T (B,E,N) -> (B,N,N)
            H_T = H.transpose(1, 2)
            A = torch.bmm(torch.bmm(H, D_e_inv), H_T)

            # 3. Propagation: A (B,N,N) @ x (B,N,F) @ W (F, Out)
            # x @ W -> (B, N, Out)
            x_w = x @ self.weight
            output = torch.bmm(A, x_w)
            return output

        else:
            raise ValueError("Incidence matrix H must be 2D or 3D.")


class GlobalAttention(nn.Module):
    """
    Computes a weighted sum of node features based on learned attention scores.
    Replaces global mean pooling. Supports masking for padded batches.
    """

    def __init__(self, in_features):
        super(GlobalAttention, self).__init__()
        # Score = V * tanh(W * x)
        self.attn_gate = nn.Linear(in_features, in_features)
        self.attn_score = nn.Linear(in_features, 1)

    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Args:
            x: Node features (Batch, N, in_features) or (N, in_features)
            mask: Boolean tensor (Batch, N). True = Real Node, False = Padding.
        Returns:
            g: Global graph embedding (Batch, in_features) or (in_features,)
        """
        is_batched = x.dim() == 3

        if not is_batched:
            # Handle single instance (N, F)
            if x.shape[0] == 0:
                return torch.zeros(self.attn_gate.in_features, device=x.device)
            x = x.unsqueeze(0)  # Fake batch dim -> (1, N, F)

        # 1. Calculate raw attention scores
        # z = tanh(W * x)
        z = torch.tanh(self.attn_gate(x))
        # scores = V * z -> (Batch, N, 1)
        scores = self.attn_score(z)

        # 2. Apply Mask (if provided)
        if mask is not None:
            # mask is (Batch, N), make it (Batch, N, 1)
            mask_expanded = mask.unsqueeze(-1)
            # Fill padding scores with -inf so Softmax makes them 0
            scores = scores.masked_fill(~mask_expanded, float('-inf'))

        # 3. Normalize scores
        weights = F.softmax(scores, dim=1)  # (Batch, N, 1)

        # 4. Weighted Sum
        # (Batch, N, 1) * (Batch, N, F) -> Sum over N -> (Batch, F)
        g = torch.sum(weights * x, dim=1)

        if not is_batched:
            return g.squeeze(0)  # Return (F,)

        return g


class FactorioHGNN(nn.Module):
    """
    The main Hypergraph Neural Network model for Factorio.
    Updated with Attention Pooling and LSTM Memory.
    """

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

        # --- 1. GNN Layers (Spatial Feature Extraction) ---
        self.hgc1 = HypergraphConv(in_features, hidden_dim)
        self.hgc2 = HypergraphConv(hidden_dim, hidden_dim)
        self.relu = nn.ReLU()

        # --- 2. Attention Layer (Spatial Focus) ---
        self.attention_pool = GlobalAttention(hidden_dim)

        # --- 3. LSTM Layer (Temporal Memory) ---
        # We use LSTMCell for efficient step-by-step processing
        self.lstm = nn.LSTMCell(input_size=hidden_dim, hidden_size=lstm_hidden_dim)

        # --- 4. Output Heads ---
        # Heads now input 'lstm_hidden_dim'
        self.action_head = nn.Sequential(
            nn.Linear(lstm_hidden_dim, lstm_hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(lstm_hidden_dim // 2, n_actions)
        )

        self.item_head = nn.Sequential(
            nn.Linear(lstm_hidden_dim, lstm_hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(lstm_hidden_dim // 2, n_items)
        )

        self.heatmap_head = nn.Sequential(
            nn.Linear(lstm_hidden_dim, lstm_hidden_dim),
            nn.ReLU(),
            nn.Linear(lstm_hidden_dim, 17 * 17)
        )

        self.rotation_head = nn.Sequential(
            nn.Linear(lstm_hidden_dim, lstm_hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(lstm_hidden_dim // 2, 4)
        )

    def forward(self,
                x: torch.Tensor,
                H: torch.Tensor,
                hidden_state: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
                mask: Optional[torch.Tensor] = None):
        """
        Args:
            x: Node features (N, F) or (Batch, N, F)
            H: Incidence matrix (N, E) or (Batch, N, E)
            hidden_state: Tuple (h, c) for LSTM.
                          If None, initializes to zeros.
            mask: (Batch, N) Boolean tensor for padding. None if single instance.

        Returns:
            action_logits, item_logits, rotation_logits, heatmap_logits, next_hidden_state
        """

        # Handle Empty Graph / Batch Initialization
        batch_size = x.shape[0] if x.dim() == 3 else 1
        device = x.device

        # Initialize hidden state if not provided
        if hidden_state is None:
            h_0 = torch.zeros(batch_size, self.lstm_hidden_dim, device=device)
            c_0 = torch.zeros(batch_size, self.lstm_hidden_dim, device=device)
            hidden_state = (h_0, c_0)

        # 1. GNN Pass
        # If single instance empty (0 nodes)
        if x.dim() == 2 and x.shape[0] == 0:
            g = torch.zeros(batch_size, self.hidden_dim, device=device)
        else:
            x_emb = self.relu(self.hgc1(x, H))
            x_emb = self.relu(self.hgc2(x_emb, H))

            # 2. Attention Pooling -> (Batch, hidden_dim)
            g = self.attention_pool(x_emb, mask=mask)

            # If input was 2D (N,F), attention returns (F,). We need (1, F) for LSTM
            if g.dim() == 1:
                g = g.unsqueeze(0)

        # 3. LSTM Pass
        # h_in: (Batch, hidden_dim), hidden_state: ((Batch, lstm_hid), (Batch, lstm_hid))
        h_n, c_n = self.lstm(g, hidden_state)
        next_hidden_state = (h_n, c_n)

        # 4. Heads
        action_logits = self.action_head(h_n)
        item_logits = self.item_head(h_n)
        rotation_logits = self.rotation_head(h_n)
        heatmap_logits_flat = self.heatmap_head(h_n)

        heatmap_logits = heatmap_logits_flat.view(batch_size, 17, 17)
        if batch_size == 1:
            # Squeeze back to (17, 17) for single instance compatibility
            heatmap_logits = heatmap_logits.squeeze(0)

            # Print predictions only for single-instance inference (debugging)
            print(f"Predicted action index: {action_logits.argmax().item()}")
            print(f"Predicted item index: {item_logits.argmax().item()}")

        return action_logits, item_logits, rotation_logits, heatmap_logits, next_hidden_state