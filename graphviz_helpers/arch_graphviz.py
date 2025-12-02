"""Graphviz export helpers for architectures produced by arch_gen."""

from __future__ import annotations

from typing import Iterable, Union

import arch_gen

try:
    import graphviz  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    graphviz = None


GraphType = Union[str, "graphviz.Digraph"]  # type: ignore


def _dedupe_by_id(elements: Iterable[arch_gen.SystemElement]) -> list[arch_gen.SystemElement]:
    unique = {}
    for element in elements:
        unique[element.element_id] = element
    return list(unique.values())


def _node_label(element: arch_gen.SystemElement) -> str:
    return f"Element {element.element_id}"


def _compute_depths(elements: Iterable[arch_gen.SystemElement]) -> dict[int, int]:
    """Assign a depth to each node based on parent-child links."""
    nodes = _dedupe_by_id(elements)
    roots = [node for node in nodes if not node.parents] or nodes[:1]
    depth: dict[int, int] = {}
    queue = [(root, 0) for root in roots]
    while queue:
        node, d = queue.pop(0)
        if node.element_id in depth and depth[node.element_id] <= d:
            continue
        depth[node.element_id] = d
        for child in _dedupe_by_id(node.children):
            queue.append((child, d + 1))
    return depth


def build_graph(
    elements: Iterable[arch_gen.SystemElement],
    include_interfaces: bool = True,
    name: str = "Architecture",
) -> GraphType:
    """Build a Graphviz Digraph (if graphviz is installed) or DOT text string."""
    nodes = _dedupe_by_id(elements)

    gv = None
    lines = [
        "digraph {",
        '  rankdir="TB";',
        '  ordering="out";',
        '  nodesep="0.4";',
        '  ranksep="0.6";',
        '  splines="ortho";',
        '  concentrate="true";',
    ]
    if graphviz:
        gv = graphviz.Digraph(  # type: ignore
            name=name,
            graph_attr={
                "rankdir": "TB",
                "ordering": "out",
                "nodesep": "0.4",
                "ranksep": "0.6",
                "splines": "ortho",
                "concentrate": "true",
            },
        )

    for element in nodes:
        label = _node_label(element).replace('"', '\"')
        if gv:
            gv.node(
                str(element.element_id),
                label,
                shape="box",
                style="rounded,filled",
                fillcolor="#e8eef7",
            )
        lines.append(
            f'  {element.element_id} [label="{label}", shape=box, style="rounded,filled", fillcolor="#e8eef7"];'
        )

    # Parent/child edges
    seen_tree_edges = set()
    for parent in nodes:
        for child in sorted(_dedupe_by_id(parent.children), key=lambda c: c.element_id):
            key = (parent.element_id, child.element_id)
            reverse_key = (child.element_id, parent.element_id)
            if reverse_key in seen_tree_edges:
                continue  # drop reciprocal edge to keep tree directed one way
            seen_tree_edges.add(key)
            if gv:
                gv.edge(str(parent.element_id), str(child.element_id), color="#222", penwidth="2")
            lines.append(f"  {parent.element_id} -> {child.element_id} [color=\"#222\", penwidth=2];")

    # Interface edges
    if include_interfaces:
        seen_interfaces = set()
        for element in nodes:
            for interface in element.interfaces:
                interface_id = id(interface)
                if interface_id in seen_interfaces:
                    continue
                seen_interfaces.add(interface_id)
                provider = getattr(interface, "p_element", None) or getattr(interface, "provides", None)
                receiver = getattr(interface, "r_element", None) or getattr(interface, "recieves", None)
                if not (provider and receiver):
                    continue
                for src, dst in ((provider, receiver), (receiver, provider)):
                    if gv:
                        gv.edge(
                            str(src.element_id),
                            str(dst.element_id),
                            color="#c0392b",
                            style="dashed",
                            constraint="false",
                        )
                    lines.append(
                        "  "
                        f"{src.element_id} -> {dst.element_id} "
                        '[color="#c0392b", style="dashed", constraint=false];'
                    )

    # Keep nodes at the same depth on the same rank for a straighter tree
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


def render_architecture(
    elements: Iterable[arch_gen.SystemElement],
    output_path: str = "architecture",
    format: str = "png",
    engine: str = "dot",
    include_interfaces: bool = True,
) -> str:
    """Render the architecture graph. Returns the path to the rendered file (or .dot)."""
    graph = build_graph(elements, include_interfaces=include_interfaces)

    if graphviz and not isinstance(graph, str):
        graph.format = format
        graph.engine = engine
        return graph.render(filename=output_path, cleanup=True)

    # Fallback: write DOT text
    dot_path = output_path if output_path.lower().endswith(".dot") else f"{output_path}.dot"
    with open(dot_path, "w", encoding="utf-8") as file:
        file.write(graph) # type: ignore
    return dot_path


if __name__ == "__main__":  # Demo usage
    elems = arch_gen.generate_architecture(3, 3)
    arch_gen.generate_interfaces(elems)
    path = render_architecture(elems, output_path="architecture_graph")
    print(f"Wrote graph to {path}")
