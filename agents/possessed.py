from agents.uninformed.villager import Villager
from agents.informed.werewolf import Werewolf
from agents.strategies.possessed_strategy import PossessedStrategy

class Possessed(Villager):

    def __init__(self):
        pass

    def init_strategy(self, base_info, diff_data, game_setting):
        self._strategy = PossessedStrategy([i for i in range(1, self._game_settings._player_num + 1)
                                            if i != self._base_info._agentIndex],
                                           self._base_info._agentIndex,
                                           self._base_info._role_map, self._player_perspective)

    def getName(self):
        return "Possessed"

    def vote(self):
        return self._strategy.vote()