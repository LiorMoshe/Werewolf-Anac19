from .agent_belief import AgentBelief


class AgentBeliefBuilder(object):
    """
    This class will be given all the information passed throughout the game
    and it will use it to update and build beliefs of all the agents in the game.
    These beliefs will be queried in the implementation of our strategy.
    """

    def __init__(self, num_agents, agent_indices):
        self._num_agents = num_agents
        self._agent_beliefs = {}

        print("Num agents: ", num_agents)
        print("Agent indices: ", agent_indices)
        for index in agent_indices:
            self._agent_beliefs[index] = AgentBelief(index)

    def update_beliefs(self, diff_data):
        """
        Given the diff data received from the server update the beliefs of the agents
        based on the sentences received from them.
        :param diff_data: Pandas dataframe showing what happened during the day, what did the agents say.
        :return: None
        """
        for i in range(len(diff_data.index)):
            curr_index = diff_data.loc[i, 'agent']

            if curr_index in self._agent_beliefs.keys():
                self._agent_beliefs[diff_data.loc[i, 'agent']].update_belief(diff_data[:(i + 1)])

