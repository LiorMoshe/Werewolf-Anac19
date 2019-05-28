from agents.uninformed.uninformed import Uninformed
from agents.information_processing.agent_strategy import TownsFolkStrategy

class Villager(Uninformed):

    def __init__(self):
        pass

    def init_strategy(self, base_info, diff_data, game_setting):
        self._strategy = TownsFolkStrategy([i for i in range(1, self._game_settings._player_num)
                            if i != self._base_info._agentIndex],
                            self._base_info._agentIndex,
                            self._base_info._role_map, self._player_perspective)

    def getName(self):
        return "Villager"

    def talk(self):
        return "Skip"

    def whisper(self):
        return ""

    def vote(self):
        return "1"

    def attack(self):
        pass

    def divine(self):
        pass

    def guard(self):
        pass

    def extract_state_info(self, base_info, diff_data, request):
        pass

