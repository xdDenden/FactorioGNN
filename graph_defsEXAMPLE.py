import math
import torch
import torch.nn as nn
import torch.nn.functional as F

class HypergraphConv(nn.Module):
    # ...existing code from original definition...
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
        De = torch.clamp(H.sum(dim=0), min=1.0)
        Dv = torch.clamp(H.sum(dim=1), min=1.0)
        Dv_inv_sqrt = torch.diag(Dv.pow(-0.5))
        De_inv = torch.diag(De.pow(-1.0))
        We = torch.diag(W_e)
        temp = H @ (We @ De_inv)
        temp = Dv_inv_sqrt @ temp
        A = temp @ (H.T @ Dv_inv_sqrt)
        out = A @ X @ self.weight
        if self.bias is not None:
            out = out + self.bias
        return out

class SimpleHGNN(nn.Module):
    # ...existing code...
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

def build_incidence_from_one_hop(edge_index, num_nodes):
    # ...existing code...
    adj = [set() for _ in range(num_nodes)]
    ei = edge_index.t().tolist()
    for u, v in ei:
        adj[u].add(v)
        adj[v].add(u)
    for i in range(num_nodes):
        adj[i].add(i)
    H = torch.zeros(num_nodes, num_nodes, dtype=torch.float32)
    for e in range(num_nodes):
        for j in adj[e]:
            H[j, e] = 1.0
    return H

