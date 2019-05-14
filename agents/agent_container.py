from agents.uninformed.villager import Villager
from agents.uninformed.seer import Seer
from agents.uninformed.bodyguard import Bodyguard
from agents.uninformed.medium import Medium
from agents.informed.werewolf import Werewolf
from agents.possessed import Possessed
from agents.logger import Logger

NO_ROLE = 'none'


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
