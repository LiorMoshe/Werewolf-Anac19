from agents.uninformed.villager import Villager
from agents.uninformed.seer import Seer
from agents.uninformed.bodyguard import Bodyguard
from agents.uninformed.medium import Medium
from agents.informed.werewolf import Werewolf
from agents.possessed import Possessed

NO_ROLE = 'none'

class AgentContainer(object):
    """
    Because the agents role is decided in run time this class will contain an agent
    and this is the agent which will be passed to the tcp client created by AIWoof.
    """

    def __init__(self, role=NO_ROLE, name='ROLTK'):
        self._role = role
        self._agent = None
        self._name = name
        self.tasks = []

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
        try:
            return self._agent.talk()
        except:
            return "OVER"

    def whisper(self):
        try:
            return self._agent.whisper()
        except:
            return "OVER"

    def vote(self):
        try:
            return self._agent.vote()
        except:
            return "1"

    def attack(self):
        try:
            return self._agent.attack()
        except:
            return "1"

    def divine(self):
        try:
            return self._agent.divine()
        except:
            return "1"

    def guard(self):
        try:
            return self._agent.guard()
        except:
            return "1"

    def finish(self):
        try:
            return self._agent.finish()
        except:
            return "1"