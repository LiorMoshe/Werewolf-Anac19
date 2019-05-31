import networkx as nx
import matplotlib.pyplot as plt
from agents.information_processing.graph_utils.group_finder import EdgeType

def color_picker(edge):
    if edge[3] == EdgeType.HATE:
        if edge[4]:
            return 'o'
        else:
            return 'r'
    else:
        if edge[4]:
            return 'g'
        else:
            return 'b'


def visualize(game_graph):
    fig = plt.figure(figsize=(12, 12))
    ax = plt.subplot(111)
    ax.set_title("Werewolf game graph")
    graph = nx.Graph()
    labels = {}
    for i in range(1, game_graph.num_nodes()):
        graph.add_node(i)
        labels[i] = str(i) + ":" + " " + str(game_graph.get_node_role(i))

    covered = []
    edge_labels = {}
    for i in range(1, 15):
        node = game_graph.get_node(i)

        for edge in node.outgoing_edges:
            if edge[1] in covered:
                continue

            edge_labels[(edge[0], edge[1])] = str(edge[2]) + '>'
            graph.add_edge(edge[0], edge[1], weight= edge[2], color=color_picker(edge))

        for edge in node.incoming_edges:
            if edge[0] in covered:
                continue
            edge_labels[edge[0], edge[1]] = str(edge[2]) + '>'
            graph.add_edge(edge[0], edge[1], weight=edge[2], color=color_picker(edge))

        for edge in node.undirected_edges:
            # if edge.from_index or edge.to_index in covered:
            #     continue

            print("Got undirecrted")
            edge_labels[edge.from_index, edge.to_index] = '<' + str(edge.weight) + '>'
            graph.add_edge(edge.from_index, edge.to_index, weight=edge.weight, color='orange' if edge.type == EdgeType.HATE else 'green')





        covered.append(i)

    pos = nx.spring_layout(graph, iterations=20)

    edges = graph.edges()
    colors = [graph[u][v]['color'] for u, v in edges]
    weights = [graph[u][v]['weight'] for u, v in edges]

    nx.draw(graph, pos, node_color='pink', node_size=600,edges=edges, edge_color=colors)
    nx.draw_networkx_labels(graph, pos, labels, font_size=6)
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=6)
    # nx.draw(graph, , node_color='green', font_size=8)
    plt.savefig("Graph.png", format="PNG")


