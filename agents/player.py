from abc import *
from enum import Enum
from agents.information_processing.agent_strategy import TownsFolkStrategy
import numpy as np

REG_VOTE = 1
RAND_VOTE = 2


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
        Contents of game info:
        Status map: Indicates which player is dead or alive in the game.
        Remain Talk Map:
        Remain Whisper Map:
        Game Role: Which role this player plays in the game.
        Agent Index: The index of the player in the game.
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
        self.log()

    def is_alive(self, index):
        return self._status_map[str(index)] == 'ALIVE'

    def log(self):
        print("Agent index is: " + str(self._agentIndex) + " his role: " + self._role)
        print("Game role map: ", self._role_map)
        print("Day in game: ", self._day)
        print("Remain Talk Map: ", self._remain_talk_map)
        print("Remain Whisper Map: ", self._remain_whisper_map)
        print("Status map: ", self._status_map)


class Task:
    def __init__(self, left, right, lweight, rweight, data):
        self.left=left
        self.right=right
        self.lweight = lweight
        self.rweight = rweight
        self.data = data
        self._len = 1

    # def insert(self, left, right, data):
    #     pass

    def len(self):
        '''
        :return: Tree height.
        '''
        return self._len

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
        self._strategy = None

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
        return self.base_info.agentIndex if self.base_info is not None else ""

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

        # Initialize the agent belief builder.
        self._strategy = TownsFolkStrategy([i for i in range(1, self._game_settings._player_num)
                                            if i != self._base_info._agentIndex],
                                           self._base_info._agentIndex,
                                           self._base_info._role_map)

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
        print("Request type: ", request)
        print("Received game diff:")
        print(diff_data.to_string())
        if request == "WHISPER":
            print("Base info: ", base_info)

        self._strategy.update(diff_data)
        self.extract_state_info(base_info)

    def reg_vote(self):
        '''
        note under vote function until fully tested
        :return:
        '''
        epsilon = 0 if len(self.tasks) == 0 else 0.3
        vote_type = np.random.choice([RAND_VOTE, REG_VOTE],p=[epsilon,1-epsilon])
        if vote_type == RAND_VOTE:
            return self.rand_vote()
        elif vote_type == REG_VOTE:
            return self.get_best_vote_opt()

    #should rename by implementation
    def rand_vote(self):
        #TODO: if tasks count is large, can try and increase max_depth
        print("Tasks count: "+len(self.tasks))
        max_depth = 3
        tasks_to_handle = []
        for t_id, task in enumerate(self.tasks):
            if task.len() > max_depth: #sanity check
                continue
            max_depth -= task.len()
            tasks_to_handle.append(t_id)
        # Draw task to handle
        t_id = np.random.choice(tasks_to_handle, p=np.ones(len(tasks_to_handle))/len(tasks_to_handle))
        # Draw agent_id - currently assume a non recursive structure
        np.random.choice([self.tasks[t_id].left, self.tasks[t_id].right],
                         p=[self.tasks[t_id].lweight, self.tasks[t_id].rweight])

    def get_best_vote_opt(self):
        '''
        :return: Id of the agent with highest vote score.
                 If several agents have the same score, chooses one randomly.
        '''
        min = -1
        agent_id = None
        for id, persp in self._strategy._perspectives.items():
            if persp.vote_score > min:
                agent_id = id
                min = persp.vote_score
            elif persp.vote_score == min:
                agent_id = np.random.choice([agent_id, id], p=[0.5,0.5])
        return agent_id

