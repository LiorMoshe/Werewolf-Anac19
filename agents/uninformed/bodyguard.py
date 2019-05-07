from .villager import Villager


class Bodyguard(Villager):

    def __init__(self):
        pass

    def getName(self):
        return "Bodyguard"

    def talk(self):
        return "COMINGOUT Agent[01] WEREWOLF"

    def whisper(self):
        return ""

    def vote(self):
        return "1"

    def attack(self):
        pass

    def divine(self):
        pass

    def guard(self):
        return "1"

    def extract_state_info(self, base_info):
        pass
