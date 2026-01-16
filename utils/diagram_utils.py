# diagram_utils.py
import matplotlib.pyplot as plt
import networkx as nx
from collections import defaultdict
import io
import base64

def generate_dfa_diagram_image(states, dfa_transitions, split_production_fn):
    G = nx.DiGraph()

    # Nodes
    for i in range(len(states)):
        G.add_node(f'I{i}')

    # Edges
    edge_labels = {}
    for (from_state, symbol), to_state in dfa_transitions.items():
        from_node = f'I{from_state}'
        to_node = f'I{to_state}'
        if not G.has_edge(from_node, to_node):
            G.add_edge(from_node, to_node)
            edge_labels[(from_node, to_node)] = symbol
        else:
            edge_labels[(from_node, to_node)] += f', {symbol}'

    plt.figure(figsize=(16, 12))

    # Layout
    layers = defaultdict(list)
    visited = set()
    queue = [(0, 0)]
    visited.add(0)
    while queue:
        state_idx, level = queue.pop(0)
        layers[level].append(f'I{state_idx}')
        for (from_state, symbol), to_state in dfa_transitions.items():
            if from_state == state_idx and to_state not in visited:
                queue.append((to_state, level + 1))
                visited.add(to_state)

    pos = {}
    for level, nodes in layers.items():
        x_pos = level * 3
        y_spacing = 2.5
        for idx, node in enumerate(nodes):
            y_pos = -(idx * y_spacing)
            pos[node] = (x_pos, y_pos)
    for i in range(len(states)):
        node = f'I{i}'
        if node not in pos:
            pos[node] = (len(layers) * 3, 0)

    # Node colors
    node_colors = []
    node_sizes = []
    for i, node in enumerate(G.nodes()):
        if node == 'I0':
            node_colors.append('#4CAF50')
            node_sizes.append(3000)
        else:
            state_idx = int(node[1:])
            has_reduce = any(dot_pos == len(split_production_fn(rhs))
                             for lhs, rhs, dot_pos in states[state_idx])
            node_colors.append('#FF5252' if has_reduce else '#2196F3')
            node_sizes.append(2500)

    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=node_sizes,
                           alpha=0.95, edgecolors='black', linewidths=2)
    nx.draw_networkx_edges(G, pos, edge_color='#555555', arrows=True,
                           arrowsize=25, width=2.5, connectionstyle='arc3,rad=0.1')
    nx.draw_networkx_labels(G, pos, font_size=14, font_weight='bold', font_color='white')

    # Edge labels
    for (u, v), label in edge_labels.items():
        x = (pos[u][0] + pos[v][0]) / 2
        y = (pos[u][1] + pos[v][1]) / 2
        dx = pos[v][0] - pos[u][0]
        dy = pos[v][1] - pos[u][1]
        length = (dx**2 + dy**2)**0.5
        if length > 0:
            offset = 0.2
            x += dy * offset / length
            y -= dx * offset / length
        plt.text(x, y, label, fontsize=11, fontweight='bold',
                 bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                           edgecolor="#888888", linewidth=1.5, alpha=0.9),
                 ha='center', va='center')

    plt.title("SLR Parser DFA - Systematic Layout", fontsize=20, fontweight='bold', pad=20)
    plt.axis('off')
    plt.tight_layout()

    buffer = io.BytesIO()
    plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    plt.close()
    return image_base64

