from agents.informed.informed import Informed
from agents.strategies.WolfStrategy import WolfStrategy


class Werewolf(Informed):

    def __init__(self):
        self.next_attack = None

    def init_strategy(self, base_info, diff_data, game_setting):
        self._strategy = WolfStrategy([i for i in range(1, self._game_settings._player_num)
                            if i != self._base_info._agentIndex],
                            self._base_info._agentIndex,
                            self._base_info._role_map, self._player_perspective)

    def getName(self):
        return "Werewolf"

    def talk(self):
        return self._strategy.generate_talk()

    def whisper(self):
        return self._strategy.whisper()

    def vote(self):
        return self._strategy.vote()

    def attack(self):
        return self._strategy.get_next_attck()

    def divine(self):
        pass

    def guard(self):
        pass

    def extract_state_info(self, base_info, diff_data, request):
        self._strategy.digest_sentences(diff_data)

