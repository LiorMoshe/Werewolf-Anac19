from agents.logger import Logger

class PlayerFame(object):
    """
    Class that holds connection of agents in the game.
    agent_likes: Indices of agents that are cooperators of this agent in the game (from his perspective).
    likes_agent: Indices of agents that see this agent as a cooperator in the game (from their perspective).
    agent_hates: Indices of agents that are enemies of this agent in the game (from his perspective).
    hates_agent: Indices of agents that see this agent as an enemy of them in the game (from their perspective).
    """

    def __init__(self, idx):

        self.idx = idx
        self.agent_likes = set()
        self.likes_agent = set()
        self.agent_hates = set()
        self.hates_agent = set()
        self.mutually_likes = set()
        self.mutually_hates = set()

    def clean(self):
        self.agent_likes = set()
        self.likes_agent = set()
        self.agent_hates = set()
        self.hates_agent = set()
        self.mutually_likes = set()
        self.mutually_hates = set()


class GroupFinder(object):

    def __init__(self, indices):
        print("Initializing fames indices: ", indices)
        self._agent_fames = {idx: PlayerFame(idx) for idx in indices}

    def find_mutual_connections(self):
        """
        Given the fames of each agent, find connections which are mutual,  meaning that both
        agents have the same feelings toward each other.
        :return:
        """
        for idx, fame in self._agent_fames.items():
            fame.mutually_likes = fame.agent_likes & fame.likes_agent
            fame.mutually_hates = fame.agent_hates & fame.hates_agent


    def find_groups(self, perspectives):
        """
        Given a list of player perspectives try to find significant groups
        within the game.
        A group can be seen as a graph, each agent is a node in the graph and it can have at most one edge
        toward other agent, the edge can show either cooperation or non-cooperation.
        :param perspectives:
        :return:
        """
        print("Finding groups")
        for index, perspective in perspectives.items():
            print("Current perspective: ", index)
            cooperators = perspective.get_cooperators()
            enemies = perspective.get_enemies()


            self._agent_fames[index].agent_likes = set(cooperators)
            self._agent_fames[index].agent_hates = set(enemies)

            for i in range(len(cooperators)):
                self._agent_fames[cooperators[i]].likes_agent.add(index)

            for i in range(len(enemies)):
                self._agent_fames[enemies[i]].hates_agent.add(index)

        self.find_mutual_connections()
        print("Finished checking groups.")

    def clean_groups(self):
        for fame in self._agent_fames.values():
            fame.clean()

    def log_groups(self):
        for idx, fame in self._agent_fames.items():
            repr_str = "<<<<<<< AGENT FAME LOG >>>>>>>>>>" + '\n'
            repr_str += "Index " + str(idx) + '\n'
            repr_str += "Agent Likes:  " + str(fame.agent_likes) + '\n'
            repr_str += "Likes Agent:  " + str(fame.likes_agent) + '\n'
            repr_str += "Agent Hates:  " + str(fame.agent_hates) + '\n'
            repr_str += "Hates Agent:  " + str(fame.hates_agent) + '\n'
            repr_str += "Mutually Likes: " + str(fame.mutually_likes) + '\n'
            repr_str += "Mutually Hates: " + str(fame.mutually_hates) + '\n'
            repr_str += " <<<<<<< End Agent Fame Log>>>" + '\n'

            Logger.instance.write(repr_str)

