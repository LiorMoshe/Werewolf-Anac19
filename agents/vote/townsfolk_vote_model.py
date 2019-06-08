from collections import namedtuple
import random

VoteUpdate = namedtuple('VoteUpdate', 'score day')

VOTE_DISCOUNT = 0.8

class VoteScore(object):

    def __init__(self):
        self._updates = []
        self._score = 0.0
        self._updated = False

    def add_update(self, vote_update):
        self._updates.append(vote_update)
        self._updated = True

    def get_score(self, day):
        if not self._updated:
            return self._score

        total = 0.0
        for update in self._updates:
            total += VOTE_DISCOUNT ** (day - update.day) * update.score

        self._score = total
        self._updated = False

        return self._score

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

        print("AGENT INDICES IN VOTERMODEL" + str(agent_indices))
        self._vote_scores = {idx: VoteScore() for idx in agent_indices}

    def update_vote(self, agent_idx, score, day):
        if agent_idx != self.index:
            self._vote_scores[agent_idx].add_update(VoteUpdate(score, day))

    def update_dead_agent(self, idx):
        del self._vote_scores[idx]

    def get_vottable_agents(self):
        return list(self._vote_scores.keys())

    def get_vote(self, day):
        max_idx = None
        max_vote_score = float('-inf')

        for idx, vote_score in self._vote_scores.items():
            curr_score = vote_score.get_score(day)
            if curr_score > max_vote_score:
                max_vote_score = curr_score
                max_idx = idx

        print("Max vote score" + str(max_vote_score))
        if max_vote_score == 0:
            return random.choice(self.get_vottable_agents())
        return max_idx

