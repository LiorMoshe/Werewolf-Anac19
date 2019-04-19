from abc import *
from enum import Enum


class GameSettings(object):
    """
    Settings of the game, this is just a bunch of static properties.
    Currently these are dummy values - will be set in set_game_settings.
    """

    def __init__(self, server_game_settings):
        self._enable_no_attack = server_game_settings['enableNoAttack']
        self._enable_no_execution = server_game_settings['enableNoExecution']
        self._enable_role_request = server_game_settings['enableRoleRequest']
        self._max_attack_revote = server_game_settings['maxAttackRevote']
        self._max_revote = server_game_settings['maxRevote']
        self._max_skip = server_game_settings['maxSkip']
        self._max_talk = server_game_settings['maxTalk']
        self._max_talk_turn = server_game_settings['maxTalkTurn']
        self._max_whisper = server_game_settings['maxWhisper']
        self._max_whisper_turn = server_game_settings['maxWhisperTurn']
        self._player_num = server_game_settings['playerNum']
        self._random_seed = server_game_settings['randomSeed']
        self._role_num_map = server_game_settings['roleNumMap']
        self._talk_on_first_day = server_game_settings['talkOnFirstDay']
        self._time_limit = server_game_settings['timeLimit']
        self._validate_utterance = server_game_settings['validateUtterance']
        self._votable_first_day = server_game_settings['votableInFirstDay']
        self._vote_visible = server_game_settings['voteVisible']
        self._whisper_before_revote = server_game_settings['whisperBeforeRevote']


class GamePhase(Enum):
    DAY = 1
    NIGHT = 2


class Request(Enum):
    """
    Represents all the available requests that we can receive from the game's server.
    """
    NAME = 1
    ROLE = 2
    INITIALIZE = 3
    DAILY_INITIALIZE = 4
    DAILY_FINISH = 5
    FINISH = 6
    VOTE = 7
    ATTACK = 8
    GUARD = 9
    DIVINE = 10
    TALK = 11
    WHISPER = 12


class GameState(object):
    """
    Defines the current state of the game as received from the server.
    """

    def __init__(self, server_base_info):
        """
        Initialize the current state of the game based on the json
        received from the server.
        :param server_base_info: JSON received from the server representing
        current state of the game.
        """
        self._agentIndex = server_base_info['agentIdx']
        self._role = server_base_info['myRole']
        self._role_map = server_base_info['roleMap']
        self._day = server_base_info['day']
        self._remain_talk_map = server_base_info['remainTalkMap']
        self._remain_whisper_map = server_base_info['remainWhisperMap']
        self._status_map = server_base_info['statusMap']


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
    def extract_state_info(self, base_info):
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
        :param base_info: Current state of the game.
        :param diff_data: Pandas dataframe that holds difference since last update.
        :param game_setting: The game settings.
        :return:
        """
        self._game_settings = GameSettings(game_setting)
        self._base_info = GameState(base_info)

    def dayStart(self):
        self._phase = GamePhase.DAY

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
        print("Received update, request type: ", request)
        request = Request[request]
        self.extract_state_info(base_info)


