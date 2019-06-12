from agents.informed.informed import Informed
from agents.strategies.agent_strategy import TownsFolkStrategy

class Werewolf(Informed):

    def __init__(self):
        pass

    def init_strategy(self, base_info, diff_data, game_setting):
        self._strategy = TownsFolkStrategy([i for i in range(1, self._game_settings._player_num)
                            if i != self._base_info._agentIndex],
                            self._base_info._agentIndex,
                            self._base_info._role_map)

    def getName(self):
        return "Werewolf"

    def talk(self):
        return "COMINGOUT Agent[01] WEREWOLF"

    def whisper(self):
        return ""

    def vote(self):
        return "1"

    def attack(self):
        return "1"

    def divine(self):
        pass

    def guard(self):
        pass

    def extract_state_info(self, base_info, diff_data, request):
        pass

