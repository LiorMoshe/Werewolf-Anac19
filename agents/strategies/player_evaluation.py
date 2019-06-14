from operator import itemgetter
from agents.tasks.request_vote_task import RequestVoteTask
from agents.logger import Logger
import random

EPSILON = 0.01


LYING_FINE = 100

WEREWOLF_FINE = 1000.


class PlayerEvaluation(object):
    """
    Holds my evaluation of other players in the game.

    EPSILON if we are sure they are HUMAN and otherwise the score can get higher if the agents either
    lie or aren't liked by my cooperators.
    Singleton - Only one instance of this in the program
    """


    class __PlayerEvaluation(object):


        def __init__(self, indices, my_idx):
            self.reset(indices, my_idx)

        def reset(self, indices, my_idx):
            self._weights = {idx: 1 for idx in indices}
            self._weights[my_idx] = EPSILON
            self.index = my_idx
            self._relevant_players = [idx for idx in indices]
            self._liars = {}
            self._last_dead_agent = None


        def player_lied(self, idx, potential_liars):
            for i in range(len(potential_liars)):
                self._liars[potential_liars[i]] = [liar for liar in potential_liars if liar != potential_liars[i]]

            self._weights[idx] += float(LYING_FINE / len(potential_liars))


        def player_is_werewolf(self, idx):
            if idx not in self._relevant_players:
                # Player died, check if he has a lying partner that needs to be redeemed.
                if idx in self._liars:
                    for potential_liar in self._liars[idx]:
                        self._weights[potential_liar] = 1

                self._weights[idx] = WEREWOLF_FINE

        def player_died(self, idx):
            """
            When players dies in vote he isn't relevant for our evaluation anymore.
            :param idx
            :return:
            """
            # We don't use list.remove because we want our relevant players object to be immutable so we create
            # a copy and remove the index from it.
            self._last_dead_agent = idx
            self._relevant_players = [player_idx for player_idx in self._relevant_players if player_idx != idx]

        def get_last_dead(self):
            return self._last_dead_agent

        def get_relevant_players(self):
            return self._relevant_players

        def players_alive(self):
            return len(self._relevant_players)

        def get_dangerous_agent(self):
            """
            Get the most dangerous agent among the relevant players.
            :return:
            """
            max_weight = float('-inf')
            max_idx = None

            for idx in self._relevant_players:
                if self._weights[idx] > max_weight:
                    max_weight = self._weights[idx]
                    max_idx = idx

            return max_idx

        def get_divine_target(self, num_candidates= 3):
            """
            Get top 3 dangerous agents and choose randomly between them.
            :return:
            """
            sorted_weights = sorted(self._weights.items(), key=itemgetter(1), reverse=True)
            candidates = []
            threshold = num_candidates

            for idx, _ in sorted_weights:
                if idx in self._relevant_players:
                    candidates.append(idx)

                    if len(candidates) == threshold:
                        break

            return random.choice(candidates)


        def player_died_werewolf(self, idx):
            """
            If a player died from wolves he is obviously a villager.
            :param idx:
            :return:
            """
            self.player_died(idx)
            self.player_in_townsfolk(idx)

        def player_in_townsfolk(self, idx):
            self._weights[idx] = EPSILON

        def thinks_im_human(self, idx):
            self._weights[idx] = min(self._weights[idx], 1 - EPSILON)

        def thinks_im_werewolf(self, idx):
            self._weights[idx] = WEREWOLF_FINE / 2

        def log(self):
            Logger.instance.write("PlayerEvaluation: " + str(self._weights))

        def get_weight(self, idx):
            try:
                return self._weights[idx]
            except KeyError:
                raise Exception("Tried getting weight of player " + str(idx) + " in PlayerEvaluation but he doesn't exist.")

        def update_evaluation(self, game_graph, day):
            """
            Given our player's node in the game graph see which players like us and which are
            dangerous to us so we have high incentive to vote for them in order to save ourselves.
            This method can create tasks of traction with the goal of requesting agents to vote for somone.
            :param game_graph: Graph of the game.
            :param day
            :return:
            """
            player_node = game_graph.get_node(self.index)
            for edge in player_node.get_incoming_edges():
                if edge.from_index in self._relevant_players:
                    if edge.is_hostile():
                        self._weights[edge.from_index] += edge.weight
                    else:
                        self._weights[edge.from_index] = max(EPSILON, self._weights[edge.from_index] - edge.weight)

            for edge in player_node.undirected_edges:
                idx = edge.from_index if edge.from_index != player_node.index else edge.to_index
                if idx in self._relevant_players:
                    if edge.is_hostile():
                        self._weights[idx] += edge.weight
                    else:
                        self._weights[idx] = max(EPSILON, self._weights[idx] - edge.weight)


            # Look at the most dangerous agent.
            dangerous_idx = self.get_dangerous_agent()
            dangerous_node = game_graph.get_node(dangerous_idx)
            Logger.instance.write("Dangerous: " + str(dangerous_idx) + " num haters: " + str(dangerous_node.num_haters()))
            # If less than third of the players don't like him, gain traction by creating a task against him.
            task = None
            if dangerous_node.num_haters() < len(self._relevant_players) / 3:
                task = RequestVoteTask(dangerous_idx, 1, day, [self.index, dangerous_idx], self.index)

            return task

        def day_passed(self):
            for idx in self._weights:
                self._weights[idx] /= 2

    instance = None

    def __init__(self, indices, my_idx):
        if not PlayerEvaluation.instance:
            PlayerEvaluation.instance = PlayerEvaluation.__PlayerEvaluation(indices, my_idx)