import os
import random
import torch
import torch.nn as nn
import torch.optim as optim
from torch_geometric.datasets import Planetoid
from torch_geometric.utils import to_networkx

# New imports from split modules
from graph_utils import save_graph_ml
from graph_defsEXAMPLE import SimpleHGNN, build_incidence_from_one_hop
from plotting import plot_confusion, compute_macro_f1, confusion_matrix

torch.manual_seed(0)
random.seed(0)

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

    # Build full graph and save with true labels
    G = to_networkx(data, to_undirected=True)
    save_graph_ml(G, data.y.cpu(), "true_label", save_path="cora_true_labels.graphml")

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

    # Save graph with predicted labels
    save_graph_ml(G, y_pred.cpu(), "pred_label", save_path="cora_pred_labels.graphml")
