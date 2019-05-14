from agents.informed.informed import Informed


class Werewolf(Informed):

    def __init__(self):
        pass

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

    def extract_state_info(self, base_info):
        pass

