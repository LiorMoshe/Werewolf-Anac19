# this code is to allow relative imports from agents directory
import os, sys
agents_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../')
# to prevent adding the directory to PYTHONPATH if already inside
if agents_dir_path not in sys.path:
    sys.path.insert(0, agents_dir_path)

from uninformed.uninformed import Uninformed


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

