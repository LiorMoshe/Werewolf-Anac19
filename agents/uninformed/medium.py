from agents.uninformed.villager import Villager
from agents.strategies.medium_straregy import MediumStrategy

# gets the identity of the voted player each day

class Medium(Villager):

    def __init__(self):
        pass

    def init_strategy(self, base_info, diff_data, game_setting):
        self._strategy = MediumStrategy([i for i in range(1, self._game_settings._player_num + 1)
                                if i != self._base_info._agentIndex],
                                self._base_info._agentIndex,
                                self._base_info._role_map,
                                base_info["statusMap"], self._player_perspective)

    def getName(self):
        return "Medium"

    def whisper(self):
        return ""

    def vote(self):
        return self._strategy.vote()

    def attack(self):
        pass

    def divine(self):
        pass

    def guard(self):
        pass

    def extract_state_info(self, base_info, diff_data, request):
        self._strategy.digest_sentences(diff_data)
