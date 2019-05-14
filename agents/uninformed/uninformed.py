# this code is to allow relative imports from agents directory
import os, sys
agents_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../')
# to prevent adding the directory to PYTHONPATH if already inside
if agents_dir_path not in sys.path:
    sys.path.insert(0, agents_dir_path)

from player import Player

class Uninformed(Player):
    """
    This is where we will implement all the functionality that is relevant to the uninformed players
    of the villager group.
    """
    pass
