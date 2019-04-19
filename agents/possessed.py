from .uninformed.villager import Villager
from .informed.werewolf import Werewolf


class Possessed(Villager, Werewolf):

    def __init__(self):
        pass

    def getName(self):
        return "Possessed"

    def talk(self):
        return ""

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

    def extract_state_info(self, base_info):
        pass
