#!/usr/bin/env python
"""
Graph-layering + per-level transformation demo.

Run:  python graph_transform.py
"""

from __future__ import annotations

import random
import re
import string
from collections import defaultdict
from dataclasses import dataclass, field
from pprint import pprint
from typing import Dict, List, Tuple

import networkx as nx

###############################################################################
# ─── Helper dataclass and utils ──────────────────────────────────────────────
###############################################################################
@dataclass
class NodeData:
    """Metadata we keep on every code-file node."""
    name: str                                     # current (possibly transformed) label
    transform_count: int = 0
    history: List[str] = field(default_factory=list)          # ["A0→a1", "a1→A2", …]
    parent_history: List[List[Tuple[str, str]]] = field(default_factory=list)
    #                       ^ one entry per transform pass (empty for level-0)

_letter_pat = re.compile(r"([A-Za-z]+)(\d+)")


def bump_name(old: str) -> str:
    """Randomly flip case of the alpha part and +1 the numeric suffix."""
    alpha, num = _letter_pat.fullmatch(old).groups()
    new_alpha = alpha.upper() if random.random() < 0.5 else alpha.lower()
    return f"{new_alpha}{int(num) + 1}"


def nth_name(i: int) -> str:
    """A, B, … Z, AA, AB, … with '0' suffix."""
    letters = ""
    while True:
        letters = string.ascii_uppercase[i % 26] + letters
        i //= 26
        if i == 0:
            break
    return f"{letters}0"


###############################################################################
# ─── 1.  Random dependency-graph generator (20-30 % density) ─────────────────
###############################################################################
def generate_graph(n: int = 12, edge_density: float = 0.25) -> nx.DiGraph:
    g = nx.DiGraph()
    # add nodes
    for i in range(n):
        nm = nth_name(i)
        g.add_node(nm, data=NodeData(name=nm))
    # add random edges
    nodes = list(g.nodes)
    for s in nodes:
        for d in nodes:
            if s == d:
                continue
            if random.random() < edge_density:
                g.add_edge(s, d)

    # guarantee at least one root
    if not [v for v in g.nodes if g.in_degree(v) == 0]:
        root_candidate = random.choice(nodes)
        for p in list(g.predecessors(root_candidate)):
            g.remove_edge(p, root_candidate)
    return g


###############################################################################
# ─── 2.  Layering with node duplication (handles cycles) ─────────────────────
###############################################################################
def layer_graph(g: nx.DiGraph) -> List[List[str]]:
    """Breadth-first layering that *duplicates* a node when reached again."""
    roots = [n for n in g.nodes if g.in_degree(n) == 0] or [random.choice(list(g.nodes))]
    levels: List[List[str]] = [roots.copy()]          # first level

    alias_count = defaultdict(int)                    # canonical → how many aliases already made
    for r in roots:
        alias_count[r] = 1

    processed_edges: set[Tuple[str, str]] = set()     # (parent, child)

    cur_level = roots
    while True:
        next_level: List[str] = []
        for alias in cur_level:
            canonical = alias.split("_")[0]
            for child in g.successors(canonical):
                if (canonical, child) in processed_edges:
                    continue
                processed_edges.add((canonical, child))

                k = alias_count[child]
                new_alias = child if k == 0 else f"{child}_{k}"
                alias_count[child] += 1
                next_level.append(new_alias)

        if not next_level:
            break
        levels.append(next_level)
        cur_level = next_level
    return levels


###############################################################################
# ─── 3.  Pretty printers ─────────────────────────────────────────────────────
###############################################################################
def graph_as_dict(g: nx.DiGraph) -> Dict[str, List[str]]:
    """Return {current_node_name: [children_current_names]}."""
    return {
        g.nodes[v]["data"].name: [g.nodes[c]["data"].name for c in g.successors(v)]
        for v in g.nodes
    }


def print_graph(g: nx.DiGraph, header: str = "") -> None:
    if header:
        print(f"\n=== {header} ===")
    pprint(graph_as_dict(g))


def print_parent_annotations(level_nodes: List[str], g: nx.DiGraph) -> None:
    """Show how parents of the *just* transformed nodes changed."""
    for alias in level_nodes:
        canon = alias.split("_")[0]
        nd: NodeData = g.nodes[canon]["data"]
        if not nd.parent_history:      # level-0 nodes
            continue
        prev_parents = nd.parent_history[-1]
        pretty = ", ".join(f"{before}→{after}" for before, after in prev_parents)
        print(f"   {nd.name}: parents [{pretty}]")


###############################################################################
# ─── 4.  Per-level transformation pass ───────────────────────────────────────
###############################################################################
def transform_levels(levels: List[List[str]], g: nx.DiGraph) -> None:
    rename_map: Dict[str, str] = {}           # canonical → most recent name

    for depth, layer in enumerate(levels):
        print(f"\n--- TRANSFORMING LEVEL {depth} ---")
        for alias in layer:
            canon = alias.split("_")[0]
            nd: NodeData = g.nodes[canon]["data"]

            old = nd.name
            new = bump_name(old)

            nd.history.append(f"{old}→{new}")
            nd.name = new
            nd.transform_count += 1
            rename_map[canon] = new

            # record how the *current* parents are now named (except for level-0)
            if depth:
                parent_pairs = [
                    (p_old := g.nodes[p]["data"].name, p_old)  # same before/after for clarity
                    for p in g.predecessors(canon)
                ]
                nd.parent_history.append(parent_pairs)

            print(f"   {alias:>8}: {old} → {new}")

        print_graph(g, f"graph after transforming up through level {depth}")
        print_parent_annotations(layer, g)


###############################################################################
# ─── 5.  History dump ────────────────────────────────────────────────────────
###############################################################################
def dump_histories(g: nx.DiGraph) -> None:
    print("\n===== FULL NODE HISTORIES =====")
    for v in sorted(g.nodes):
        nd: NodeData = g.nodes[v]["data"]
        print(f"{v}:")
        print(f"   transforms ({nd.transform_count}): {nd.history}")
        for idx, par in enumerate(nd.parent_history, 1):
            parents_pretty = ", ".join(f"{b}→{a}" for b, a in par)
            print(f"   step {idx} parent map: [{parents_pretty}]")


###############################################################################
# ─── 6.  Demo run ────────────────────────────────────────────────────────────
###############################################################################
if __name__ == "__main__":
    random.seed(42)                                 # make runs reproducible

    G = generate_graph(n=12, edge_density=0.25)

    print_graph(G, "ORIGINAL GRAPH (A0, B0, …)")

    lvls = layer_graph(G)
    for i, l in enumerate(lvls):
        print(f"Level {i}: {', '.join(l)}")

    transform_levels(lvls, G)

    print_graph(G, "FINAL TRANSFORMED GRAPH")
    dump_histories(G)
