
EPSILON = 0.01


LYING_FINE = 2

class PlayerEvaluation(object):
    """
    Holds my evaluation of other players in the game.

    EPSILON if we are sure they are HUMAN and otherwise the score can get higher if the agents either
    lie or aren't liked by my cooperators.
    Singleton - Only one instance of this in the program
    """


    class __PlayerEvaluation(object):


        def __init__(self, indices, my_idx):
            print("INIT")
            self._weights = {idx: 1 for idx in indices}
            self._weights[my_idx] = EPSILON
            self._relevant_players = [idx for idx in indices]

        def player_lied(self, idx, num_potential_liars):
            self._weights[idx] += float(LYING_FINE / num_potential_liars)

        def player_died(self, idx):
            """
            When players dies in vote he isn't relevant for our evaluation anymore.
            :param idx
            :return:
            """
            # We don't use list.remove because we want our relevant players object to be immutable so we create
            # a copy and remove the index from it.
            self._relevant_players = [player_idx for player_idx in self._relevant_players if player_idx != idx]

        def get_relevant_players(self):
            return self._relevant_players

        def player_died_werewolf(self, idx):
            """
            If a player died from wolves he is obviously a villager.
            :param idx:
            :return:
            """
            self.player_died(idx)
            self._weights[idx] = EPSILON

        def get_weight(self, idx):
            try:
                return self._weights[idx]
            except KeyError:
                raise Exception("Tried getting weight of player " + str(idx) + " in PlayerEvaluation but he doesn't exist.")



    instance = None

    def __init__(self, indices, my_idx):
        if not PlayerEvaluation.instance:
            PlayerEvaluation.instance = PlayerEvaluation.__PlayerEvaluation(indices, my_idx)