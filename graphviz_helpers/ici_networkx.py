"""NetworkX export helpers for ICI hierarchies (parent/child only).

Build a NetworkX DiGraph from an ICI head node (or iterable of ICIs) and
optionally render it with matplotlib or export an interactive HTML via pyvis.
"""

from __future__ import annotations

import json
from typing import Any, Iterable, Protocol, Union

import networkx as nx

try:
    import matplotlib.pyplot as plt  # type: ignore
except ImportError:  # pragma: no cover
    plt = None

try:
    from pyvis.network import Network  # type: ignore
except ImportError:  # pragma: no cover
    Network = None


class SupportsICI(Protocol):
    node_id: int
    children: list["SupportsICI"]
    system_elements: list[Any]  # objects with element_id


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
    if hasattr(nodes, "node_id") and not isinstance(nodes, Iterable):
        return _collect_descendants(nodes)  # type: ignore[arg-type]
    # Deduplicate by node_id
    seen: dict[int, SupportsICI] = {}
    for node in nodes:  # type: ignore[assignment]
        seen[node.node_id] = node
    return list(seen.values())


def build_ici_nx(
    nodes: Union[SupportsICI, Iterable[SupportsICI]],
    include_elements: bool = True,
) -> nx.DiGraph:
    """Return a NetworkX DiGraph for the ICI hierarchy."""
    nodes_list = _normalize_nodes(nodes)
    G = nx.DiGraph()
    for node in nodes_list:
        elements = getattr(node, "system_elements", [])
        element_ids = [getattr(e, "element_id", "?") for e in elements]
        attrs = {
            "label": f"ICI {node.node_id}",
            "elements": element_ids if include_elements else [],
        }
        G.add_node(node.node_id, **attrs)

    for parent in nodes_list:
        for child in getattr(parent, "children", []) or []:
            G.add_edge(child.node_id, parent.node_id)  # child -> parent direction
    return G


def build_system_element_nx(
    elements: list,
    include_interfaces: bool = True,
) -> nx.DiGraph:
    """
    Return a NetworkX DiGraph for SystemElement architecture.

    Args:
        elements: List of SystemElement objects
        include_interfaces: Whether to include interface edges

    Returns:
        NetworkX DiGraph with:
        - Nodes representing SystemElements
        - Solid edges for parent-child relationships
        - Dotted red edges for interfaces (if include_interfaces=True)
    """
    G = nx.DiGraph()

    # Add all nodes
    for elem in elements:
        attrs = {
            "label": f"SE {elem.element_id}",
            "functions": getattr(elem, "functions", []),
            "capabilities": getattr(elem, "capabilities", []),
            "element_type": "system_element"
        }
        G.add_node(elem.element_id, **attrs)

    # Add parent-child edges (hierarchy)
    for elem in elements:
        for child in getattr(elem, "children", []):
            G.add_edge(
                child.element_id,
                elem.element_id,
                edge_type="hierarchy",
                color="#666",
                style="solid"
            )

    # Add interface edges (dependencies)
    if include_interfaces:
        for elem in elements:
            for interface in getattr(elem, "interfaces", []):
                # Interface goes from provider to receiver
                provider_id = interface.p_element.element_id
                receiver_id = interface.r_element.element_id

                # Avoid self-loops and duplicates
                if provider_id != receiver_id and not G.has_edge(provider_id, receiver_id):
                    G.add_edge(
                        provider_id,
                        receiver_id,
                        edge_type="interface",
                        color="#ff0000",
                        style="dashed",
                        p_function=interface.p_function,
                        r_function=interface.r_function,
                        r_capability=interface.r_capability,
                        ver_type=type(interface.ver_type).__name__
                    )

    return G


def draw_ici_matplotlib(G: nx.DiGraph, path: str | None = None) -> None:
    """Quick visualization using matplotlib; spring_layout fallback."""
    if plt is None:
        raise RuntimeError("matplotlib is not installed")
    pos = nx.spring_layout(G, seed=42)
    labels = {n: f"{n}" for n in G.nodes()}
    nx.draw(G, pos, with_labels=False, node_color="#e8eef7", edge_color="#222", arrows=True)
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=8)
    if path:
        plt.savefig(path, bbox_inches="tight")
    else:
        plt.show()
    plt.clf()


def _compute_hierarchical_layout(G: nx.DiGraph) -> dict[int, dict[str, float]]:
    """
    Compute hierarchical positions based on the directed graph structure.
    Edges go child->parent, so:
    - Parents (top): nodes with NO outgoing edges (they don't point to anyone)
    - Children (bottom): nodes WITH outgoing edges pointing up to parents
    """
    if not G.nodes():
        return {}

    # Find parent/root nodes (no outgoing edges - ultimate parents at top)
    roots = [n for n in G.nodes() if G.out_degree(n) == 0]
    if not roots:
        # If no clear roots, pick nodes with minimum out-degree
        min_degree = min(G.out_degree(n) for n in G.nodes())
        roots = [n for n in G.nodes() if G.out_degree(n) == min_degree]

    # Assign levels using BFS from roots, traversing BACKWARDS through edges
    levels: dict[int, int] = {}
    queue = [(r, 0) for r in roots]
    visited = set()

    while queue:
        node, level = queue.pop(0)
        if node in visited:
            continue
        visited.add(node)
        levels[node] = level

        # Add children (nodes that point TO this parent - traverse backwards)
        for child in G.predecessors(node):
            if child not in visited:
                queue.append((child, level + 1))

    # Handle any unvisited nodes
    for node in G.nodes():
        if node not in levels:
            levels[node] = 0

    # Group nodes by level
    level_groups: dict[int, list[int]] = {}
    for node, level in levels.items():
        if level not in level_groups:
            level_groups[level] = []
        level_groups[level].append(node)

    # Compute positions
    positions = {}
    level_height = 150  # vertical spacing between levels
    node_spacing = 120  # horizontal spacing between nodes

    for level, nodes in level_groups.items():
        y = level * level_height
        # Center nodes horizontally at this level
        total_width = (len(nodes) - 1) * node_spacing
        start_x = -total_width / 2

        for i, node in enumerate(sorted(nodes)):  # sort for consistency
            x = start_x + i * node_spacing
            positions[node] = {"x": x, "y": y}

    return positions


def export_ici_pyvis(G: nx.DiGraph, html_path: str = "ici_network.html") -> str:
    """
    Export an interactive HTML. Tries pyvis; if unavailable/broken, writes a minimal vis.js HTML.
    Returns the output path.
    """
    # Compute hierarchical layout based on the graph structure
    nodes_with_pos = _compute_hierarchical_layout(G)

    # Store positions in graph attributes
    for nid, pos in nodes_with_pos.items():
        G.nodes[nid]["x"] = pos["x"]
        G.nodes[nid]["y"] = pos["y"]

    # Preferred: pyvis
    if Network is not None:
        try:
            net = Network(directed=True, height="750px", width="100%", notebook=False)
            net.toggle_physics(False)
            # Build nodes/edges manually to preserve coordinates but allow dragging
            for nid, data in G.nodes(data=True):
                elements = data.get("elements", [])
                functions = data.get("functions", [])
                capabilities = data.get("capabilities", [])
                element_type = data.get("element_type", "ici")

                # Build tooltip based on node type
                if element_type == "system_element":
                    title_lines = [f"SE {nid}"]
                    if functions:
                        title_lines.append("Functions: " + ", ".join(map(str, functions)))
                    if capabilities:
                        title_lines.append("Capabilities: " + ", ".join(map(str, capabilities)))
                else:
                    # ICI node
                    title_lines = [f"ICI {nid}"]
                    if elements:
                        title_lines.append(f"System Elements ({len(elements)}): " + ", ".join(map(str, elements)))

                coords = nodes_with_pos.get(nid, {"x": 0, "y": 0})
                net.add_node(
                    nid,
                    label=str(nid),
                    title="<br>".join(title_lines),
                    x=coords["x"],
                    y=coords["y"],
                    physics=False,
                )
            for src, dst in G.edges():
                net.add_edge(src, dst, arrows="to")
            net.set_options(
                """
                var options = {
                  interaction: {
                    dragNodes: true,
                    dragView: true,
                    zoomView: true
                  },
                  physics: false,
                  edges: { arrows: { to: { enabled: true } } }
                };
                """
            )
            net.write_html(html_path, open_browser=False, notebook=False)
            return html_path
        except Exception:
            # Fall through to vis.js fallback
            pass

    # Fallback: minimal vis.js HTML
    nodes_data = []
    for nid, data in G.nodes(data=True):
        elements = data.get("elements", [])
        functions = data.get("functions", [])
        capabilities = data.get("capabilities", [])
        element_type = data.get("element_type", "ici")

        # Build title based on node type
        if element_type == "system_element":
            title_parts = [f"SE {nid}"]
            if functions:
                title_parts.append("Functions: " + ", ".join(map(str, functions)))
            if capabilities:
                title_parts.append("Capabilities: " + ", ".join(map(str, capabilities)))
        else:
            # ICI node
            title_parts = [f"ICI {nid}"]
            if elements:
                title_parts.append(f"System Elements ({len(elements)}): " + ", ".join(map(str, elements)))

        title = "\\n".join(title_parts)
        coords = nodes_with_pos.get(nid, {"x": 0, "y": 0})
        nodes_data.append(
            {
                "id": nid,
                "label": str(nid),
                "title": title,
                "x": coords["x"],
                "y": coords["y"],
            }
        )

    # Separate edges by type
    edges_data = []
    for src, dst, data in G.edges(data=True):
        edge_type = data.get("edge_type", "hierarchy")
        edge_info = {
            "from": src,
            "to": dst,
            "arrows": "to"
        }

        if edge_type == "interface":
            edge_info["color"] = {"color": "#ff0000", "highlight": "#ff4444"}
            edge_info["dashes"] = True
            edge_info["width"] = 2
            edge_info["id"] = f"interface_{src}_{dst}"

            # Add interface details to title
            p_func = data.get("p_function", "")
            r_func = data.get("r_function", "")
            r_cap = data.get("r_capability", "")
            ver_type = data.get("ver_type", "")
            title_parts = [f"Interface: {src} → {dst}"]
            if p_func:
                title_parts.append(f"Provides: {p_func}")
            if r_func:
                title_parts.append(f"Requires: {r_func}")
            if r_cap:
                title_parts.append(f"Capability: {r_cap}")
            if ver_type:
                title_parts.append(f"Verification: {ver_type}")
            edge_info["title"] = "\\n".join(title_parts)
        else:
            # Hierarchy edge
            edge_info["color"] = {"color": "#666", "highlight": "#2b7ce9"}
            edge_info["dashes"] = False
            edge_info["width"] = 2
            edge_info["id"] = f"hierarchy_{src}_{dst}"

        edges_data.append(edge_info)

    # Detect graph characteristics for UI
    has_interfaces = any(e.get("dashes") for e in edges_data)
    node_types = set(data.get("element_type", "ici") for _, data in G.nodes(data=True))
    is_system_elements = "system_element" in node_types

    graph_type = "System Element Network" if is_system_elements else "ICI Integration Chain"
    edge_description = "Solid edges = hierarchy | Dotted red edges = interfaces" if has_interfaces else "Edges show parent → child relationships"
    show_interface_toggle = has_interfaces

    # Properly serialize JSON
    nodes_json = json.dumps(nodes_data)
    edges_json = json.dumps(edges_data)

    html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>{graph_type}</title>
  <script type="text/javascript" src="https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.js"></script>
  <link href="https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.css" rel="stylesheet" type="text/css" />
  <style>
    body {{
      margin: 0;
      padding: 20px;
      font-family: Arial, sans-serif;
      background: #f5f5f5;
    }}
    #network {{
      border: 1px solid #ddd;
      border-radius: 4px;
      background: white;
    }}
    .info {{
      margin-bottom: 10px;
      padding: 10px;
      background: #e3f2fd;
      border-radius: 4px;
      border-left: 4px solid #2b7ce9;
    }}
    .controls {{
      margin-bottom: 15px;
      padding: 10px;
      background: white;
      border-radius: 4px;
      border: 1px solid #ddd;
    }}
    .controls button {{
      padding: 8px 16px;
      margin-right: 10px;
      background: #2b7ce9;
      color: white;
      border: none;
      border-radius: 4px;
      cursor: pointer;
      font-size: 14px;
      transition: background 0.2s;
    }}
    .controls button:hover {{
      background: #1a5bb8;
    }}
    .controls button:active {{
      background: #14478a;
    }}
    #selectionCount {{
      color: #2b7ce9;
    }}
  </style>
</head>
<body>
  <div class="info">
    <strong>{graph_type}</strong> (Hierarchical Layout)<br>
    📍 <strong>Click node</strong> to select (Ctrl/Cmd+Click for multi-select)<br>
    🎯 <strong>Drag on background</strong> to draw selection box<br>
    🔄 <strong>Drag selected nodes</strong> to move them together<br>
    🔍 <strong>Mouse wheel</strong> to zoom in/out<br>
    ✋ <strong>Click background</strong> to deselect all<br>
    💡 <strong>Hover over nodes</strong> to see details<br>
    <em>{edge_description}</em>
  </div>
  <div class="controls">
    <button id="selectAll" title="Select all nodes">Select All</button>
    <button id="deselectAll" title="Deselect all nodes">Deselect All</button>
    {"<button id=\"toggleInterfaces\" title=\"Show/hide interface edges\" style=\"margin-left: 20px;\">Hide Interfaces</button>" if show_interface_toggle else ""}
    <span id="selectionCount" style="margin-left: 15px; font-weight: bold;">Selected: 0</span>
  </div>
  <div id="network" style="height: 800px;"></div>
  <script type="text/javascript">
    const nodes = new vis.DataSet({nodes_json});
    const edges = new vis.DataSet({edges_json});
    const container = document.getElementById('network');
    const data = {{
      nodes: nodes,
      edges: edges
    }};
    const options = {{
      layout: {{
        hierarchical: false
      }},
      physics: {{
        enabled: false
      }},
      interaction: {{
        dragNodes: true,
        dragView: true,
        zoomView: true,
        hover: true,
        multiselect: true,
        selectConnectedEdges: false,
        tooltipDelay: 200
      }},
      nodes: {{
        shape: 'box',
        margin: 10,
        widthConstraint: {{
          minimum: 60,
          maximum: 120
        }},
        color: {{
          background: '#e8eef7',
          border: '#2b7ce9',
          highlight: {{
            background: '#ffd700',
            border: '#ff8c00'
          }}
        }},
        borderWidth: 2,
        borderWidthSelected: 4,
        font: {{
          size: 14,
          color: '#222',
          bold: {{
            color: '#000'
          }}
        }},
        shadow: {{
          enabled: true,
          color: 'rgba(0,0,0,0.15)',
          size: 5,
          x: 2,
          y: 2
        }}
      }},
      edges: {{
        arrows: {{
          to: {{
            enabled: true,
            scaleFactor: 0.8,
            type: 'arrow'
          }}
        }},
        color: {{
          color: '#666',
          highlight: '#2b7ce9',
          hover: '#2b7ce9'
        }},
        width: 2,
        smooth: {{
          type: 'cubicBezier',
          forceDirection: 'vertical',
          roundness: 0.5
        }},
        shadow: {{
          enabled: true,
          color: 'rgba(0,0,0,0.1)',
          size: 3,
          x: 1,
          y: 1
        }}
      }}
    }};
    const network = new vis.Network(container, data, options);

    // Track selection and interface visibility
    let selectedNodes = [];
    let interfacesVisible = true;

    // Get interface edge IDs
    const interfaceEdges = {edges_json}
      .filter(e => e.id && e.id.startsWith('interface_'))
      .map(e => e.id);

    // Update selection count display
    function updateSelectionCount() {{
      selectedNodes = network.getSelectedNodes();
      document.getElementById('selectionCount').textContent = `Selected: ${{selectedNodes.length}}`;
    }}

    // Toggle interfaces visibility (only if toggle button exists)
    const toggleButton = document.getElementById('toggleInterfaces');
    if (toggleButton) {{
      toggleButton.addEventListener('click', function() {{
        interfacesVisible = !interfacesVisible;

        if (interfacesVisible) {{
          // Show interfaces
          interfaceEdges.forEach(edgeId => {{
            edges.update({{id: edgeId, hidden: false}});
          }});
          toggleButton.textContent = 'Hide Interfaces';
          toggleButton.style.background = '#2b7ce9';
        }} else {{
          // Hide interfaces
          interfaceEdges.forEach(edgeId => {{
            edges.update({{id: edgeId, hidden: true}});
          }});
          toggleButton.textContent = 'Show Interfaces';
          toggleButton.style.background = '#ff6b6b';
        }}
      }});
    }}

    // Selection changed event
    network.on('selectNode', function(params) {{
      updateSelectionCount();
    }});

    network.on('deselectNode', function(params) {{
      updateSelectionCount();
    }});

    network.on('select', function(params) {{
      updateSelectionCount();
    }});

    // Select All button
    document.getElementById('selectAll').addEventListener('click', function() {{
      const allNodeIds = nodes.getIds();
      network.selectNodes(allNodeIds);
      updateSelectionCount();
    }});

    // Deselect All button
    document.getElementById('deselectAll').addEventListener('click', function() {{
      network.unselectAll();
      updateSelectionCount();
    }});

    // Click on canvas to deselect
    network.on('click', function(params) {{
      if (params.nodes.length === 0) {{
        network.unselectAll();
        updateSelectionCount();
      }}
    }});

    // Log drag events (optional - for debugging)
    network.on('dragEnd', function(params) {{
      if (params.nodes.length > 0) {{
        const selected = network.getSelectedNodes();
        if (selected.length > 1) {{
          console.log(`Moved ${{selected.length}} nodes together`);
        }}
        params.nodes.forEach(function(nodeId) {{
          const position = network.getPositions([nodeId])[nodeId];
          console.log('Node ' + nodeId + ' moved to:', position);
        }});
      }}
    }});

    // Initial count
    updateSelectionCount();
  </script>
</body>
</html>"""
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    return html_path


if __name__ == "__main__":  # Demo stub
    print("Import build_ici_nx, draw_ici_matplotlib, or export_ici_pyvis and pass your ICIs.")