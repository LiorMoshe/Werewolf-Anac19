import random
from agents.logger import Logger
from operator import itemgetter

class TownsfolkVoteModel(object):
    """
    This model holds all the logic that helps a Townsfolk player decide who to vote
    for. This is used in the TownsfolkStrategy when we have to decide who to vote for.

    The vote of the simple villager constitutes of two major factors:
    1. How likely does he think the agent is one of the werewolf team.
    2. How likely the rest of the players think this player is part of the werewolf team.

    If we think someone is one the werewolf team but nobody is sure of it and we will be the only one voting
    for him we will waste our vote and probably put us in danger for nothing.
    """

    def __init__(self, agent_indices, my_idx):
        self.index = my_idx
        self._vote_scores = {idx:0 for idx in agent_indices}

    def update_vote(self, agent_idx, score):
        if agent_idx != self.index:
            self._vote_scores[agent_idx] += score

    def clear_scores(self):
        for idx in self._vote_scores.keys():
            self._vote_scores[idx] = 0.0

    def set_to_max_score(self, agent_idx):
        max_score = max(self._vote_scores.items(), key=itemgetter(1))[1]
        self._vote_scores[agent_idx] = abs(max_score) * 2

    def update_dead_agent(self, idx):
        """
        When an agent dies we don't want to consider him in the voting system anymore.
        :param idx:
        :return:
        """
        del self._vote_scores[idx]

    def get_vottable_agents(self):
        return list(self._vote_scores.keys())

    def get_vote(self):
        Logger.instance.write("Current voting scores: " + str(self._vote_scores))
        max_idx, max_vote_score = max(self._vote_scores.items(), key=itemgetter(1))

        Logger.instance.write("Max vote score " + str(max_vote_score) + " for index: " + str(max_idx))
        if max_vote_score == 0:
            return random.choice(self.get_vottable_agents())
        return max_idx

    def handle_vote_request(self, game_graph, requested_from, target):
        """
        Handle a request from some agent to vote to a given agent.
        We will listen to this agent only if he is a really good cooperator of ours.
        :param game_graph:
        :param requested_from:
        :param target
        :return:
        """
        Logger.instance.write("Agent" + str(requested_from) + " requested from us to vote for Agent" + str(target))

        top_cooperators = game_graph.get_node(self.index).get_top_k_cooperators(k=3)
        if requested_from in top_cooperators:
            Logger.instance.write("Requesting agent is a cooperator, maxing out his vote request")
            self.set_to_max_score(target)

class PossessedVoteModel(TownsfolkVoteModel):
    def get_vote(self):
        min_idx, min_vote_score = min(self._vote_scores.items(), key=itemgetter(1))
        if min_vote_score == 0:
            return random.choice(self.get_vottable_agents())
        return min_idx