# this code is to allow relative imports from agents directory
import os, sys
agents_dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.')
# to prevent adding the directory to PYTHONPATH if already inside
if agents_dir_path not in sys.path:
    sys.path.insert(0, agents_dir_path)

from uninformed.villager import Villager
from uninformed.seer import Seer
from uninformed.bodyguard import Bodyguard
from uninformed.medium import Medium
from informed.werewolf import Werewolf
from possessed import Possessed

NO_ROLE = 'none'

print("ok")
class AgentContainer(object):
    """
    Because the agents role is decided in run time this class will contain an agent
    and this is the agent which will be passed to the tcp client created by AIWoof.
    """

    def __init__(self, role=NO_ROLE, name='Dummy'):
        self._role = role
        self._agent = None
        self._name = name

    def getName(self):
        return self._name

    def initialize(self, base_info, diff_data, game_setting):
        """
        Initialization should be common between all players.
        :param base_info: Current state of the game.
        :param diff_data: Pandas dataframe that holds difference since last update.
        :param game_setting: The game settings.
        :return:
        """
        if self._role == NO_ROLE:
            self._role = base_info['myRole']

        if self._role == 'VILLAGER':
            self._agent = Villager()
        elif self._role == 'WEREWOLF':
            self._agent = Werewolf()
        elif self._role == 'SEER':
            self._agent = Seer()
        elif self._role == 'BODYGUARD':
            self._agent = Bodyguard()
        elif self._role == 'MEDIUM':
            self._agent = Medium()
        elif self._role == 'POSSESSED':
            self._agent = Possessed()

        self._agent.initialize(base_info, diff_data, game_setting)

    def update(self, base_info, diff_data, request):
        self._agent.update(base_info, diff_data, request)

    def dayStart(self):
        self._agent.dayStart()

    def talk(self):
        return self._agent.talk()

    def whisper(self):
        return self._agent.whisper()

    def vote(self):
        return self._agent.vote()

    def attack(self):
        return self._agent.attack()

    def divine(self):
        return self._agent.divine()

    def guard(self):
        return self._agent.guard()

    def finish(self):
        return self._agent.finish()
