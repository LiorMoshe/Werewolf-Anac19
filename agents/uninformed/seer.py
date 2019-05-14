# this code is to allow relative imports from agents directory
import os, sys
agents_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../')
# to prevent adding the directory to PYTHONPATH if already inside
if agents_dir_path not in sys.path:
    sys.path.insert(0, agents_dir_path)

from uninformed.villager import Villager


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


