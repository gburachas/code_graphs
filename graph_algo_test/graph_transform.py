#!/usr/bin/env python
"""Dependency-graph transformer (parents = in-edges)."""

from __future__ import annotations
import random, re, string
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pprint import pprint
from typing import Dict, List, Tuple
import networkx as nx

###############################################################################
# ─── helpers ─────────────────────────────────────────────────────────────────
###############################################################################
@dataclass
class NodeData:
    name: str
    n_transforms: int = 0
    history: List[str] = field(default_factory=list)           # ["A0→a1", …]
    parent_history: List[List[Tuple[str, str]]] = field(default_factory=list)

_pat = re.compile(r"([A-Za-z]+)(\d+)")
def bump(old: str) -> str:
    alpha, num = _pat.fullmatch(old).groups()
    alpha = alpha.upper() if random.random() < .5 else alpha.lower()
    return f"{alpha}{int(num)+1}"

def nth(i: int) -> str:                         # A0, B0, … Z0, AA0, …
    s = ""
    while True:
        s = string.ascii_uppercase[i % 26] + s
        i //= 26
        if i == 0: break
    return f"{s}0"

###############################################################################
# ─── 1. random dependency graph (≈25 % density, reproducible) ────────────────
###############################################################################
def make_graph(n: int = 12, dens: float = 0.25, *, seed: int | None = None) -> nx.DiGraph:
    """
    Generate a random directed dependency graph.

    Parameters
    ----------
    n     : number of nodes
    dens  : edge-density target (≈ probability of any A→B edge)
    seed  : int | None
        If an int is supplied, `random.seed(seed)` is called so the exact same
        graph is produced every time you run the script with that seed.
        If None (default) the graph is different on each run.
    """
    if seed is not None:
        random.seed(seed)

    g = nx.DiGraph()

    # add nodes
    for i in range(n):
        nm = nth(i)
        g.add_node(nm, data=NodeData(name=nm))

    # add edges  (A → B  ==  “B imports A”)
    for s in g:
        for d in g:
            if s != d and random.random() < dens:
                g.add_edge(s, d)

    # ensure at least one root (in-degree 0)
    if not [v for v in g if g.in_degree(v) == 0]:
        v = random.choice(list(g))
        g.remove_edges_from([(p, v) for p in list(g.predecessors(v))])

    return g


###############################################################################
# ─── 2.  adjacency helpers (parents vs. children) ────────────────────────────
###############################################################################
def children_dict(g) -> Dict[str, List[str]]:
    return {g.nodes[v]['data'].name:       # current names
            [g.nodes[c]['data'].name for c in g.successors(v)] for v in g}

def parents_dict(g) -> Dict[str, List[str]]:
    return {g.nodes[v]['data'].name:
            [g.nodes[p]['data'].name for p in g.predecessors(v)] for v in g}


###############################################################################
# ─── 3.  build levels using ONLY the parents view ────────────────────────────
###############################################################################
def build_levels(g: nx.DiGraph) -> List[List[str]]:
    """Kahn-style layering based on *parents* (in-edges)."""
    indeg = {v: g.in_degree(v) for v in g}
    level0 = [v for v, d in indeg.items() if d == 0]
    levels: List[List[str]] = [level0.copy()]

    alias_cnt = defaultdict(int)                # canonical → alias counter
    for v in level0: alias_cnt[v] = 1

    queue = deque(level0)
    while queue:
        cur_alias = queue.popleft()
        cur_can   = cur_alias.split('_')[0]

        for child in g.successors(cur_can):     # downstream dependents
            indeg[child] -= 1
            if indeg[child] == 0:
                k = alias_cnt[child]
                new_alias = child if k == 0 else f"{child}_{k}"
                alias_cnt[child] += 1
                lvl_idx = max(idx for idx,l in enumerate(levels) if cur_alias in l) + 1
                if len(levels) <= lvl_idx:
                    levels.append([])
                levels[lvl_idx].append(new_alias)
                queue.append(new_alias)

        # cycle-breaker: if queue emptied but indeg not all 0
        if not queue and any(d > 0 for d in indeg.values()):
            stuck = next(v for v,d in indeg.items() if d > 0)
            indeg[stuck] = 0
            alias_cnt[stuck] = 1 if alias_cnt[stuck]==0 else alias_cnt[stuck]
            new_alias = stuck if alias_cnt[stuck]==1 else f"{stuck}_{alias_cnt[stuck]-1}"
            levels.append([new_alias])
            queue.append(new_alias)
    return levels

###############################################################################
# ─── 4.  per-level transform (driven by parents) ─────────────────────────────
###############################################################################
def transform(levels, g):
    current: Dict[str, str] = {}          # canonical → latest name

    for depth, layer in enumerate(levels):
        print(f"\n--- TRANSFORMING LEVEL {depth} (|layer|={len(layer)}) ---")
        for alias in layer:
            canon = alias.split('_')[0]
            nd = g.nodes[canon]['data']

            old, new = nd.name, bump(nd.name)
            nd.name, nd.n_transforms = new, nd.n_transforms + 1
            nd.history.append(f"{old}→{new}")
            current[canon] = new

            # --- record direct-parent mapping (only for non-root levels) -------
            if depth:
                parent_pairs = []
                for p in g.predecessors(canon):
                    p_data = g.nodes[p]['data']
                    # original name = first entry in history *if it exists*,
                    # otherwise whatever the parent is currently called
                    orig = (
                        p_data.history[0].split('→')[0]
                        if p_data.history else p_data.name
                    )
                    parent_pairs.append((orig, current.get(p, p_data.name)))
                nd.parent_history.append(parent_pairs)

            print(f"{alias:>10}: {old} → {new}")

        print("\nparents view after level", depth)
        pprint(parents_dict(g))
        print("\nchildren view after level", depth)
        pprint(children_dict(g))


###############################################################################
# ─── 5.  history dump ────────────────────────────────────────────────────────
###############################################################################
def dump(g):
    print("\n===== FULL NODE HISTORIES =====")
    for v in sorted(g):
        nd = g.nodes[v]['data']
        print(f"{v}:")
        print(f"   transforms ({nd.n_transforms}): {nd.history}")
        for i, ph in enumerate(nd.parent_history,1):
            print(f"   step {i} parents: "
                  f"{', '.join(f'{b}→{a}' for b,a in ph)}")


###############################################################################
# ─── 6.  demo run ─────────────────────────────────────────────────────────────
###############################################################################
if __name__ == "__main__":
    random.seed(42)

    G = make_graph(12, .1, seed=42)

    print("\n=== ORIGINAL parents-dict (dependencies) ===")
    pprint(parents_dict(G))
    print("\n=== ORIGINAL children-dict (dependents) ===")
    pprint(children_dict(G))

    lvls = build_levels(G)
    for i,l in enumerate(lvls):
        print(f"Level {i}: {', '.join(l)}")

    transform(lvls, G)

    print("\n=== FINAL parents-dict ===")
    pprint(parents_dict(G))
    print("\n=== FINAL children-dict ===")
    pprint(children_dict(G))

    dump(G)
