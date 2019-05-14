from agents.uninformed.villager import Villager


class Seer(Villager):

    def __init__(self):
        pass

    def talk(self):
        print("Called  TALK")
        if self._base_info.is_alive(1):
            return "COMINGOUT Agent[01] WEREWOLF"
        elif self._base_info.is_alive(2):
            return "COMINGOUT Agent[02] WEREWOLF"
        elif self._base_info.is_alive(3):
            return "COMINGOUT Agent[03x] WEREWOLF"

    def whisper(self):
        return ""

    def vote(self):
        return "1"

    def attack(self):
        pass

    def divine(self):
        return "1"

    def guard(self):
        pass

    def extract_state_info(self, base_info):
        pass


