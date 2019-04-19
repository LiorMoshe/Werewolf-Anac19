from .villager import Villager


class Bodyguard(Villager):

    def __init__(self):
        pass

    def getName(self):
        return "Bodyguard"

    def talk(self):
        return ""

    def whisper(self):
        return ""

    def vote(self):
        pass

    def attack(self):
        pass

    def divine(self):
        pass

    def guard(self):
        pass

    def extract_state_info(self, base_info):
        pass
