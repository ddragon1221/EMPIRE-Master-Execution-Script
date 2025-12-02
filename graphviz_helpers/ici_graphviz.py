"""Graphviz export helpers for ICI hierarchies (parent/child only)."""

from __future__ import annotations

from typing import Iterable, Protocol, Union
from collections.abc import Iterable as CollIterable

try:
    import graphviz  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    graphviz = None


class SupportsICI(Protocol):
    node_id: int
    children: list["SupportsICI"]
    system_elements: list[object]  # objects with element_id


GraphType = Union[str, "graphviz.Digraph"]  # type: ignore


def _collect_descendants(head: SupportsICI) -> list[SupportsICI]:
    """BFS collect a head node and all descendants."""
    collected: dict[int, SupportsICI] = {}
    queue = [head]
    while queue:
        node = queue.pop(0)
        if node.node_id in collected:
            continue
        collected[node.node_id] = node
        for child in getattr(node, "children", []) or []:
            queue.append(child)
    return list(collected.values())


def _normalize_nodes(nodes: Union[SupportsICI, Iterable[SupportsICI]]) -> list[SupportsICI]:
    """Accept a single head or an iterable of nodes."""
    if hasattr(nodes, "node_id") and not isinstance(nodes, CollIterable):
        return _collect_descendants(nodes)  # type: ignore[arg-type]
    return _dedupe_by_id(nodes)  # type: ignore[arg-type]


def _dedupe_by_id(nodes: Iterable[SupportsICI]) -> list[SupportsICI]:
    seen = {}
    for node in nodes:
        seen[node.node_id] = node
    return list(seen.values())


def _find_roots(nodes: Iterable[SupportsICI]) -> list[SupportsICI]:
    nodes = list(nodes)
    child_ids = {child.node_id for node in nodes for child in node.children}
    roots = [node for node in nodes if node.node_id not in child_ids]
    return roots or nodes[:1]


def _compute_depths(nodes: Iterable[SupportsICI]) -> dict[int, int]:
    """Assign depth using parent->child links; roots are depth 0."""
    nodes = _dedupe_by_id(nodes)
    roots = _find_roots(nodes)
    depth: dict[int, int] = {}
    queue = [(root, 0) for root in roots]
    while queue:
        node, d = queue.pop(0)
        if node.node_id in depth and depth[node.node_id] <= d:
            continue
        depth[node.node_id] = d
        for child in _dedupe_by_id(node.children):
            queue.append((child, d + 1))
    return depth


def _node_label(node: SupportsICI, include_elements: bool = True) -> str:
    if not include_elements:
        return f"ICI {node.node_id}"
    elements = getattr(node, "system_elements", [])
    element_ids = [getattr(e, "element_id", "?") for e in elements]
    if not element_ids:
        return f"ICI {node.node_id}\nElements: (none)"
    # Wrap element ids across lines to avoid overly wide nodes
    per_line = 4
    chunks = [element_ids[i : i + per_line] for i in range(0, len(element_ids), per_line)]
    chunk_lines = [", ".join(map(str, chunk)) for chunk in chunks]
    return f"ICI {node.node_id}\nElements:\n" + "\n".join(chunk_lines)


def build_graph(
    nodes: Union[SupportsICI, Iterable[SupportsICI]],
    name: str = "ICI",
    include_elements: bool = True,
) -> GraphType:
    """Build a Graphviz Digraph (if graphviz installed) or DOT text string."""
    nodes = _normalize_nodes(nodes)

    gv = None
    lines = [
        "digraph {",
        '  rankdir="LR";',
        '  ordering="out";',
        '  nodesep="0.4";',
        '  ranksep="0.7";',
        '  splines="ortho";',
        '  concentrate="true";',
    ]
    if graphviz:
        gv = graphviz.Digraph(  # type: ignore
            name=name,
            graph_attr={
                "rankdir": "LR",
                "ordering": "out",
                "nodesep": "0.4",
                "ranksep": "0.7",
                "splines": "ortho",
                "concentrate": "true",
            },
        )

    for node in nodes:
        label = _node_label(node, include_elements=include_elements).replace('"', '\\"')
        if gv:
            gv.node(
                str(node.node_id),
                label,
                shape="box",
                style="rounded,filled",
                fillcolor="#e8eef7",
            )
        lines.append(
            f'  {node.node_id} [label="{label}", shape=box, style="rounded,filled", fillcolor="#e8eef7"];'
        )

    seen_edges = set()
    for parent in nodes:
        for child in sorted(_dedupe_by_id(parent.children), key=lambda c: c.node_id):
            key = (child.node_id, parent.node_id)
            if key in seen_edges:
                continue
            seen_edges.add(key)
            if gv:
                gv.edge(str(child.node_id), str(parent.node_id), color="#222", penwidth="2")
            lines.append(f"  {child.node_id} -> {parent.node_id} [color=\"#222\", penwidth=2];")

    depths = _compute_depths(nodes)
    ranks: dict[int, list[int]] = {}
    for node_id, d in depths.items():
        ranks.setdefault(d, []).append(node_id)
    for d, ids in sorted(ranks.items()):
        rank_line = "  { rank=same; " + " ".join(str(i) for i in sorted(ids)) + " };"
        lines.append(rank_line)
        if gv:
            gv.body.append("{ rank=same; " + " ".join(str(i) for i in sorted(ids)) + " }")

    lines.append("}")
    return gv if gv else "\n".join(lines)


def render_ici(
    nodes: Union[SupportsICI, Iterable[SupportsICI]],
    output_path: str = "ici_architecture",
    format: str = "png",
    engine: str = "dot",
    include_elements: bool = True,
) -> str:
    """Render the ICI hierarchy graph. Returns the path to the rendered file (or .dot)."""
    graph = build_graph(nodes, include_elements=include_elements)

    if graphviz and not isinstance(graph, str):
        graph.format = format
        graph.engine = engine
        return graph.render(filename=output_path, cleanup=True)

    dot_path = output_path if output_path.lower().endswith(".dot") else f"{output_path}.dot"
    with open(dot_path, "w", encoding="utf-8") as file:
        file.write(graph)
    return dot_path


if __name__ == "__main__":  # Demo stub; expects existing ICINode instances
    print("Import render_ici and pass your ICI nodes to render.")
