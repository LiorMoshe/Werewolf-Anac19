from agents.logger import Logger
from enum import Enum


class EdgeType(Enum):
    LIKE = 1,
    HATE = 2


# noinspection PyAttributeOutsideInit
class PlayerNode(object):
    """
    Class that holds connection of agents in the game.
    """

    def __init__(self, idx):
        self.index = idx

        # Use the role for visualization
        self.role = None
        self.clean()

    def update_mutual_edges(self):
        """
        Go over all of the outgoing and incoming edges and find undirected edges.
        :return:
        """
        common = []
        for first_edge in self.outgoing_edges.keys():
            for second_edge in self.incoming_edges.keys():
                if first_edge[0] == second_edge[1] and first_edge[1] == second_edge[0] and \
                        first_edge[3] == second_edge[3] and first_edge[4] == second_edge[4]:
                    common.append((GameGraph.Edge(*first_edge), GameGraph.Edge(*second_edge)))

        self.undirected_edges = set()
        for edge_tuple in common:
            del self.outgoing_edges[edge_tuple[0].get_hashable_type()]
            del self.incoming_edges[edge_tuple[1].get_hashable_type()]

            self.undirected_edges.add(GameGraph.Edge.get_as_multi_directional(*edge_tuple))

    def set_up_references(self, player_nodes):
        for idx, node in player_nodes.items():
            self.edges_references[idx] = node

    def is_connected(self):
        return len(self.undirected_edges) != 0 or len(self.outgoing_edges) != 0 or len(self.incoming_edges) != 0

    def clean(self):
        self.outgoing_edges = {}
        self.incoming_edges = {}
        self.undirected_edges = set()
        self.edges_references = {}


class GameGraph(object):
    """
    Representation of the graph of the game.
    """

    def __init__(self):
        self._nodes = {}

    def num_nodes(self):
        return len(self._nodes)

    def get_node_role(self, node_idx):
        return self._nodes[node_idx].role

    class Edge(object):

        def __init__(self, from_index, to_index, weight, edge_type, multi_directional=False):
            self.from_index = from_index
            self.to_index = to_index
            self.weight = weight
            self.type = edge_type
            self.multi_directional = multi_directional

        def get_hashable_type(self):
            """
            In order to use an edge as a key in a map it has to be a hashable type, we will map
            edges based on the indices of players that this edge connects (a tuple is a hashable type
            so we can use it as a key in our dictionary)
            :return:
            """
            return self.from_index, self.to_index, self.weight, self.type, self.multi_directional

        @staticmethod
        def get_as_multi_directional(first_edge, second_edge):
            """
            Given two edges combine them to a multi-directional edge with a weight that is equal
            to the sum of weights of both edges.
            :param first_edge:
            :param second_edge:
            :return:
            """
            return GameGraph.Edge(first_edge.from_index, first_edge.to_index,
                                  first_edge.weight + second_edge.weight, first_edge.type, True)

        def __str__(self):
            return "(" + str(self.from_index) + ", " + str(self.to_index) + ") Type:" + str(self.type) + " Weight: " \
                   + str(self.weight)

    def add_node(self, node):
        if node.index not in self._nodes.keys():
            self._nodes[node.index] = node

    def get_node(self, idx):
        try:
            return self._nodes[idx]
        except KeyError:
            return None

    def finalize_graph(self):
        """
        Add references to neighbors in all the nodes in the graph.
        :return:
        """
        for idx, node in self._nodes.items():
            if node.is_connected():
                node.set_up_references(self._nodes)
        return self

    def get_connected_components(self):
        """
        Get connected components in the graph.
        :return:
        """
        pass

    def log(self):
        repr_str = "<<<<<< GameGraph Log >>>>>>>>>" + '\n' * 2
        for idx, node in self._nodes.items():
            repr_str += '\t' + "<<<<<<< Graph Node " + str(idx) + " >>>>>" + '\n' * 2
            repr_str += '\t' + "Incoming Edges \n"
            repr_str += Logger.log_list(get_edges(list(node.incoming_edges.keys())), prefix_tabs=2)
            repr_str += '\n'
            repr_str += '\t' + "Outgoing Edges: \n"
            repr_str += Logger.log_list( get_edges(list(node.outgoing_edges.keys())), prefix_tabs=2)
            repr_str += '\n'
            repr_str += '\t' + "Undirected Edges: \n"
            repr_str += Logger.log_list(node.undirected_edges, prefix_tabs=2)
            repr_str += '\n'
            repr_str += '\t' + "<<<<<<< End Graph Node >>>" + '\n' * 2

        repr_str += "<<<<< End GameGraph Log >>>>" + '\n'
        Logger.instance.write(repr_str)


def get_edges(hashable_types):
    edges = []
    for member in hashable_types:
        edges.append(GameGraph.Edge(*member))
    return edges


class GroupFinder(object):

    def __init__(self, indices):
        self._agents_nodes = {idx: PlayerNode(idx) for idx in indices}
        self._player_roles = {}

    def set_player_role(self, idx, role):
        self._player_roles[idx] = role


    def find_mutual_connections(self):
        """
        Given the fames of each agent, find connections which are mutual,  meaning that both
        agents have the same feelings toward each other.
        :return:
        """
        for idx, node in self._agents_nodes.items():
            node.update_mutual_edges()

    def find_groups(self, perspectives, day):
        """
        Given a list of player perspectives try to find significant groups
        within the game.
        A group can be seen as a graph, each agent is a node in the graph and it can have at most one edge
        toward other agent, the edge can show either cooperation or non-cooperation.
        :param perspectives:
        :param day
        :return:
        """
        for index, perspective in perspectives.items():
            self.update_edges(index, perspective.get_cooperators(), EdgeType.LIKE,
                              lambda cooperator: cooperator.get_fondness(day))
            self.update_edges(index, perspective.get_enemies(), EdgeType.HATE,
                              lambda enemy: enemy.get_hostility(day))

        self.find_mutual_connections()
        return self.build_graph()

    def update_edges(self, from_index, nodes, edge_type, get_weight_func):
        for to_index, node in nodes.items():
            curr_edge = GameGraph.Edge(from_index, to_index, get_weight_func(node), edge_type)
            self._agents_nodes[to_index].incoming_edges[curr_edge.get_hashable_type()] = curr_edge.weight
            self._agents_nodes[from_index].outgoing_edges[curr_edge.get_hashable_type()] = curr_edge.weight

    def build_graph(self):
        """
        Given the agent fames build the final game graph.
        :return:
        """
        graph = GameGraph()
        for index, node in self._agents_nodes.items():
            if index in self._player_roles.keys():
                node.role = self._player_roles[index]
            graph.add_node(node)
        return graph.finalize_graph()

    def clean_groups(self):
        for node in self._agents_nodes.values():
            node.clean()