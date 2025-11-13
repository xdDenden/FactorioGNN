import math
import numpy as np
import matplotlib.pyplot as plt
import torch
import networkx as nx

def plot_graph(G, labels, save_path, title, cmap=plt.cm.tab10):
    # ...existing code (moved)...
    def _separate_positions(pos_dict, nodelist, min_dist=10.0, iterations=30):
        P = np.array([pos_dict[n] for n in nodelist], dtype=np.float64)
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
                                d = np.random.uniform(-1.0, 1.0, size=2)
                                dist = np.hypot(d[0], d[1]) + 1e-9
                            push = (min_dist - dist) * 0.5
                            step = (d / dist) * push
                            P[i] -= step
                            P[j] += step
                            moved += 1
            if moved == 0:
                break
            P = np.clip(P, 0.0, 1.0)
        P = P * spans + mins
        return {n: (float(P[k, 0]), float(P[k, 1])) for k, n in enumerate(nodelist)}

    n = G.number_of_nodes()
    plt.figure(figsize=(10, 10))
    pos = nx.spring_layout(G, seed=42, k=1.0 / math.sqrt(max(n, 1)), iterations=100)
    nodelist = list(range(n))
    unique_labels = sorted(set(labels.tolist()))
    color_map = {lbl: cmap(i % cmap.N) for i, lbl in enumerate(unique_labels)}
    node_colors = [color_map[int(labels[nid].item())] for nid in nodelist]
    pos = _separate_positions(pos, nodelist=nodelist, min_dist=0.02, iterations=35)
    nx.draw(G, pos, nodelist=nodelist, node_size=5, width=0.2,
            with_labels=False, node_color=node_colors, edge_color="k")
    plt.title(title)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(save_path, dpi=500)
    plt.close()
    print(f"Saved graph plot to {save_path}")

def confusion_matrix(y_true, y_pred, num_classes):
    # ...existing code...
    cm = torch.zeros(num_classes, num_classes, dtype=torch.int64)
    for t, p in zip(y_true.tolist(), y_pred.tolist()):
        cm[t, p] += 1
    return cm

def compute_macro_f1(y_true, y_pred, num_classes):
    # ...existing code...
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

def compute_accuracy(y_true, y_pred):
    return (y_true == y_pred).float().mean().item()

def plot_confusion(cm, acc, save_path):
    # ...existing code...
    import matplotlib.pyplot as plt
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
