from agents.uninformed.uninformed import Uninformed


class Villager(Uninformed):

    def __init__(self):
        pass

    def getName(self):
        return "Villager"

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
        pass

    def extract_state_info(self, base_info):
        pass

