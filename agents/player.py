from abc import *
from enum import Enum


class GameSettings(object):
    """
    Settings of the game, this is just a bunch of static properties.
    Currently these are dummy values - will be set in set_game_settings.
    """

    maxRevote = 0

    randomSeed = 0

    validateUtterance = True

    enableNoExecution = False

    roleNumMap = {}

    votableInFirstDay = False

    maxSkip = 0

    timeLimit = -1

    maxWhisper = 0

    maxWhisperTurn = 0

    whisperBeforeRevote = False

    maxTalkTurn = 20

    playerNum = 5

    voteVisible = True

    maxAttackRevote = 1

    talkOnFirstDay = False

    enableNoAttack = False

    maxTalk = 10


class GamePhase(Enum):
    DAY = 1
    NIGHT = 2


class BaseInfo(object):
    """
    Defines the current state of the game as received from the server.
    """


class Player(ABC):
    """
    Base player class, contains all the common properties to all the players in the game like the
    game settings, game phase (either day or night) etc.
    """

    def __init__(self):
        """
        The initial game settings and current state of the game are initialized to be empty.
        """
        self._game_settings = None
        self._base_info = None
        self._phase = GamePhase.DAY

    @property
    def game_settings(self):
        """
        Parse the game settings received from the server.
        :param settings:
        :return:
        """
        return self._game_settings

    @property
    def game_phase(self):
        """
        Defines current phase of the game either night or day.
        :return:
        """
        return self._phase

    @property
    def base_info(self):
        """

        :return:
        """
        return self._base_info

    @abstractmethod
    def extract_state_info(self):
        """
        Each agent will extract relevant information from the
        given state which will be received from the game's server.
        There are certain fields that are only relevant for werewolfs
        or villagers.
        Will be called on each update() call of the agent.
        :return:
        """
        pass

    @abstractmethod
    def getName(self):
        pass

    def initialize(self, base_info, diff_data, game_setting):
        """
        Initialization should be common between all players.
        :param base_info:
        :param diff_data:
        :param game_setting:
        :return:
        """
        self.base_info

    def dayStart(self):
        pass

    @abstractmethod
    def talk(self):
        pass

    @abstractmethod
    def whisper(self):
        pass

    @abstractmethod
    def vote(self):
        pass

    @abstractmethod
    def attack(self):
        pass

    @abstractmethod
    def divine(self):
        pass

    @abstractmethod
    def guard(self):
        pass

    def finish(self):
        pass

    def update(self, base_info, diff_data, request):
        pass


