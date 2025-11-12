# hgnn_cora.py
# HGNN on Cora dataset: Train/test split, train HGNN, save plots
# Run: python hgnn_cora.py

import os
import math
import random
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

from torch_geometric.datasets import Planetoid
from torch_geometric.utils import to_networkx

torch.manual_seed(0)
random.seed(0)

# -------------------------------
# Hypergraph layers and model
# -------------------------------
class HypergraphConv(nn.Module):
    """
    One hypergraph convolution layer (HGNN: Feng et al. 2019).
    X' = Dv^{-1/2} H We De^{-1} H^T Dv^{-1/2} X Theta
    H: (N,E) incidence matrix; We defaults to identity if None.
    """
    def __init__(self, in_feats, out_feats, bias=True):
        super().__init__()
        self.weight = nn.Parameter(torch.Tensor(in_feats, out_feats))
        if bias:
            self.bias = nn.Parameter(torch.Tensor(out_feats))
        else:
            self.register_parameter('bias', None)
        self.reset_parameters()

    def reset_parameters(self):
        nn.init.kaiming_uniform_(self.weight, a=math.sqrt(5))
        if self.bias is not None:
            fan_in = self.weight.size(0)
            bound = 1 / math.sqrt(fan_in)
            nn.init.uniform_(self.bias, -bound, bound)

    def forward(self, X, H, W_e=None):
        N, E = H.shape
        if W_e is None:
            W_e = torch.ones(E, device=X.device, dtype=X.dtype)

        De = torch.clamp(H.sum(dim=0), min=1.0)   # (E,)
        Dv = torch.clamp(H.sum(dim=1), min=1.0)   # (N,)

        Dv_inv_sqrt = torch.diag(Dv.pow(-0.5))
        De_inv = torch.diag(De.pow(-1.0))
        We = torch.diag(W_e)

        temp = H @ (We @ De_inv)      # (N, E)
        temp = Dv_inv_sqrt @ temp     # (N, E)
        A = temp @ (H.T @ Dv_inv_sqrt)  # (N, N)

        out = A @ X @ self.weight
        if self.bias is not None:
            out = out + self.bias
        return out

class SimpleHGNN(nn.Module):
    def __init__(self, in_feats, hidden, n_classes, dropout=0.5):
        super().__init__()
        self.conv1 = HypergraphConv(in_feats, hidden)
        self.conv2 = HypergraphConv(hidden, n_classes)
        self.dropout = dropout

    def forward(self, X, H, W_e=None):
        x = self.conv1(X, H, W_e)
        x = F.relu(x)
        x = F.dropout(x, p=self.dropout, training=self.training)
        x = self.conv2(x, H, W_e)
        return x

# -------------------------------
# Utilities
# -------------------------------
def build_incidence_from_one_hop(edge_index, num_nodes):
    """
    Build H (N x N): one hyperedge per node, containing the node and its 1-hop neighbors.
    """
    adj = [set() for _ in range(num_nodes)]
    ei = edge_index.t().tolist()
    for u, v in ei:
        adj[u].add(v)
        adj[v].add(u)
    for i in range(num_nodes):
        adj[i].add(i)  # include self

    H = torch.zeros(num_nodes, num_nodes, dtype=torch.float32)
    for e in range(num_nodes):
        for j in adj[e]:
            H[j, e] = 1.0
    return H

def plot_graph(G, labels, save_path, title, cmap=plt.cm.tab10):
    """
    Plot a NetworkX graph G with node colors from labels tensor.
    Enforces a small minimum distance between nodes to avoid overlapping dots.
    """
    def _separate_positions(pos_dict, nodelist, min_dist=10.0, iterations=30):
        # Convert to array (n,2)
        P = np.array([pos_dict[n] for n in nodelist], dtype=np.float64)
        # Normalize to [0,1] box for stable stepping
        mins = P.min(axis=0)
        spans = np.maximum(P.max(axis=0) - mins, 1e-9)
        P = (P - mins) / spans

        cell = max(min_dist, 1e-4)
        neigh_offsets = [(dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)]

        for _ in range(iterations):
            bins = {}
            idxs = np.floor(P / cell).astype(int)
            for i, c in enumerate(map(tuple, idxs)):
                bins.setdefault(c, []).append(i)

            moved = 0
            for i, ci in enumerate(map(tuple, idxs)):
                pi = P[i]
                for dx, dy in neigh_offsets:
                    nbr_cell = (ci[0] + dx, ci[1] + dy)
                    if nbr_cell not in bins:
                        continue
                    for j in bins[nbr_cell]:
                        if j <= i:
                            continue
                        pj = P[j]
                        d = pj - pi
                        dist = np.hypot(d[0], d[1])
                        if dist < min_dist:
                            if dist < 1e-9:
                                # random tiny nudge if identical
                                d = np.random.uniform(-1.0, 1.0, size=2)
                                dist = np.hypot(d[0], d[1]) + 1e-9
                            push = (min_dist - dist) * 0.5
                            step = (d / dist) * push
                            P[i] -= step
                            P[j] += step
                            moved += 1
            if moved == 0:
                break
            # keep within [0,1]
            P = np.clip(P, 0.0, 1.0)

        # Denormalize back
        P = P * spans + mins
        return {n: (float(P[k, 0]), float(P[k, 1])) for k, n in enumerate(nodelist)}

    n = G.number_of_nodes()
    plt.figure(figsize=(10, 10))

    # Compute initial layout
    pos = nx.spring_layout(G, seed=42, k=1.0 / math.sqrt(max(n, 1)), iterations=100)

    # Consistent node order and colors
    nodelist = list(range(n))
    unique_labels = sorted(set(labels.tolist()))
    color_map = {lbl: cmap(i % cmap.N) for i, lbl in enumerate(unique_labels)}
    node_colors = [color_map[int(labels[nid].item())] for nid in nodelist]

    # Enforce minimal separation between nodes (dots won't overlap)
    pos = _separate_positions(pos, nodelist=nodelist, min_dist=0.02, iterations=35)

    nx.draw(
        G,
        pos,
        nodelist=nodelist,
        node_size=5,
        width=0.2,
        with_labels=False,
        node_color=node_colors,
        edge_color="k",
    )
    plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(save_path, dpi=500)
    plt.close()
    print(f"Saved graph plot to {save_path}")

def confusion_matrix(y_true, y_pred, num_classes):
    cm = torch.zeros(num_classes, num_classes, dtype=torch.int64)
    for t, p in zip(y_true.tolist(), y_pred.tolist()):
        cm[t, p] += 1
    return cm

def compute_macro_f1(y_true, y_pred, num_classes):
    f1s = []
    for c in range(num_classes):
        tp = ((y_pred == c) & (y_true == c)).sum().item()
        fp = ((y_pred == c) & (y_true != c)).sum().item()
        fn = ((y_pred != c) & (y_true == c)).sum().item()
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        f1s.append(f1)
    return sum(f1s) / len(f1s) if f1s else 0.0

def plot_confusion(cm, acc, save_path):
    plt.figure(figsize=(6, 5))
    plt.imshow(cm, interpolation='nearest', cmap=plt.cm.Blues)
    plt.title(f'HGNN on Cora - Test Acc: {acc:.4f}')
    plt.colorbar()
    num_classes = cm.shape[0]
    ticks = list(range(num_classes))
    plt.xticks(ticks, ticks)
    plt.yticks(ticks, ticks)
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.tight_layout()
    plt.savefig(save_path, dpi=200)
    plt.close()
    print(f"Saved confusion matrix to {save_path}")

# -------------------------------
# Main: Load Cora, build H, train/test HGNN, plot results
# -------------------------------
if __name__ == "__main__":
    # Load Cora with the exact snippet requested
    dataset = Planetoid(root=os.path.expanduser('~/somewhere/Cora'), name='Cora')
    data = dataset[0]
    print(f'Dataset: {dataset}:')
    print('======================')
    print(f'Number of graphs: {len(dataset)}')
    print(f'Number of features: {dataset.num_features}')
    print(f'Number of classes: {dataset.num_classes}')
    print(f'Number of nodes: {data.num_nodes}')
    print(f'Number of edges: {data.num_edges}')
    print(f'Average node degree: {data.num_edges / data.num_nodes:.2f}')
    print(f'Number of training nodes: {data.train_mask.sum()}')
    print(f'Training node label rate: {int(data.train_mask.sum()) / data.num_nodes:.2f}')
    print(f'Contains isolated nodes: {data.contains_isolated_nodes()}')
    print(f'Contains self-loops: {data.contains_self_loops()}')
    print(f'Is undirected: {data.is_undirected()}')

    # Build full graph and plot (colored by true labels)
    G = to_networkx(data, to_undirected=True)
    plot_graph(G, data.y.cpu(), save_path="cora_graph.png", title="Cora (true labels)")

    # Build hypergraph incidence matrix H from 1-hop neighborhoods
    H = build_incidence_from_one_hop(data.edge_index, data.num_nodes)

    # Random train/test split
    N = data.num_nodes
    idx = torch.randperm(N)
    train_ratio = 0.7
    n_train = int(train_ratio * N)
    train_idx = idx[:n_train]
    test_idx = idx[n_train:]

    # Prepare tensors and model
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    X = data.x.to(device)
    Y = data.y.to(device)
    H = H.to(device)

    model = SimpleHGNN(in_feats=dataset.num_features, hidden=64, n_classes=dataset.num_classes, dropout=0.5).to(device)
    optimizer = optim.Adam(model.parameters(), lr=0.01, weight_decay=5e-4)
    loss_fn = nn.CrossEntropyLoss()

    # Train
    epochs = 50
    for epoch in range(1, epochs + 1):
        model.train()
        logits = model(X, H)
        loss = loss_fn(logits[train_idx], Y[train_idx])
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if epoch % 10 == 0 or epoch == 1:
            with torch.no_grad():
                pred = logits.argmax(dim=1)
                train_acc = (pred[train_idx] == Y[train_idx]).float().mean().item()
                test_acc = (pred[test_idx] == Y[test_idx]).float().mean().item()
            print(f"Epoch {epoch:03d} | Loss {loss.item():.4f} | Train acc {train_acc:.4f} | Test acc {test_acc:.4f}")

    # Evaluate
    model.eval()
    with torch.no_grad():
        logits = model(X, H)
        y_pred = logits.argmax(dim=1)
        test_acc = (y_pred[test_idx] == Y[test_idx]).float().mean().item()
        macro_f1 = compute_macro_f1(Y[test_idx].cpu(), y_pred[test_idx].cpu(), dataset.num_classes)
        print(f"Final Test Accuracy: {test_acc:.4f}")
        print(f"Final Macro F1: {macro_f1:.4f}")

    # Plots of results
    cm = confusion_matrix(Y[test_idx].cpu(), y_pred[test_idx].cpu(), dataset.num_classes)
    plot_confusion(cm.numpy(), test_acc, save_path="cora_hgnn_confusion.png")

    # Plot graph colored by predicted labels
    plot_graph(G, y_pred.cpu(), save_path="cora_graph_pred.png", title="Cora (predicted labels)")
