import networkx as nx
from typing import Union, Sequence

def save_graph_ml(G, labels: Union[Sequence, 'torch.Tensor'], label_name: str, save_path: str):
    """
    Attach node labels (predicted or true) to a copy of G and write as GraphML.
    labels: 1D tensor/list/array aligned with integer node ids.
    """
    # Accept torch tensor without importing torch at module top to stay lightweight
    try:
        import torch
        if isinstance(labels, torch.Tensor):
            labels_list = labels.view(-1).tolist()
        else:
            labels_list = list(labels)
    except ImportError:
        labels_list = list(labels)

    G_copy = G.copy()
    for i, node in enumerate(G_copy.nodes()):
        if i < len(labels_list):
            G_copy.nodes[node][label_name] = str(int(labels_list[i]))
        else:
            G_copy.nodes[node][label_name] = "0"
    nx.write_graphml(G_copy, save_path)
    print(f"Saved graph to {save_path}")

