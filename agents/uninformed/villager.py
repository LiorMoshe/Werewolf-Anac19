from .informed import Informed


class Villager(Informed):

    def __init__(self):
        pass

    def getName(self):
        return "Villager"

    def initialize(self, base_info, diff_data, game_setting):
        pass

    def dayStart(self):
        pass

    def talk(self):
        pass

    def whisper(self):
        pass

    def vote(self):
        pass

    def attack(self):
        pass

    def divine(self):
        pass

    def guard(self):
        pass

    def finish(self):
        pass

    def update(self, base_info, diff_data, request):
        pass
