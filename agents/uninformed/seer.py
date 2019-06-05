from agents.uninformed.villager import Villager
from agents.information_processing.strategies.SeerStrategy import SeerStrategy

class Seer(Villager):

    def __init__(self):
        pass

    def init_strategy(self, base_info, diff_data, game_setting):
        self._strategy = SeerStrategy([i for i in range(1, self._game_settings._player_num)
                                if i != self._base_info._agentIndex],
                                self._base_info._agentIndex,
                                self._base_info._role_map,
                                base_info["statusMap"], self._player_perspective)

    def talk(self):
        print("Called  TALK")
        return self._strategy.talk()

    def whisper(self):
        return ""

    def vote(self):
        return self._strategy.vote()

    def attack(self):
        pass

    def divine(self):
        return self._strategy.get_next_divine()

    def guard(self):
        pass

    def extract_state_info(self, base_info, diff_data, request):
        self._strategy.digest_sentences(diff_data)

