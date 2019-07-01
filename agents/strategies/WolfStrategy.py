from agents.information_processing.agent_perspective import *
from agents.information_processing.message_parsing import *
from agents.information_processing.sentences_container import SentencesContainer
from agents.information_processing.graph_utils.group_finder import  GroupFinder
from agents.information_processing.graph_utils.visualization import visualize
from agents.states.base_state import BaseState
from agents.information_processing.dissection.sentence_dissector import SentenceDissector
from agents.states.day_one import DayOne
from agents.information_processing.lie_detector import LieDetector
from agents.tasks.task_manager import TaskManager
from agents.vote.townsfolk_vote_model import TownsfolkVoteModel
from agents.states.state_type import StateType
from agents.strategies.player_evaluation import PlayerEvaluation
from agents.strategies.role_estimations import RoleEstimations
from agents.tasks.guard_task import GuardTask
from agents.tasks.vote_task import VoteTask
from agents.tasks.divine_task import DivineTask
from agents.tasks.identify_task import IdentifyTask
import numpy as np


# These sentences currently, don't help us much (maybe will be used in future dev).
UNUSEFUL_SENTENCES = ['Skip', 'Over']


class MessageType(Enum):
    """
    All the different message types we can receive from the server.
    TALK - Sentence has been sent by the agent.
    VOTE - The agent has given the following vote.
    EXECUTE - The agent has been executed (based on the votes).
    DEAD - The agent has been killed by the werewolves during the night.
    ATTACK_VOTE - The agent is a werewolf cooperator of ours (we will see this message only when we are in
    the werewolves group).
    FINISH - This is when the all players reveal their real identities.
    """
    TALK = 1,
    VOTE = 2,
    EXECUTE = 3,
    DEAD = 4,
    ATTACK_VOTE = 5,
    ATTACK = 6,
    WHISPER = 7,
    FINISH = 8,
    DIVINE = 9


class WolfStrategy(object):
    """
    This will be  a townsfolk player strategy, we will hold a perspective for all the players in the game.
    In the case of a player of the werewolf group we need to append to this strategy another perspective that
    inspects moves of werewolves teammates through the night and day.
    """

    def __init__(self, agent_indices, my_index, role_map):
        self._perspectives = {}
        self._teammates = {}
        self._message_parser = MessageParser()
        self._sentences_container = SentencesContainer()
        # for idx in agent_indices:
        #     self._perspectives[idx] = AgentPerspective(idx, my_index, self._sentences_container,
        #                                                None if idx not in role_map.keys() else role_map[idx])
        for idx in agent_indices:
            self._perspectives[idx] = AgentPerspective(idx, my_index, len(agent_indices) + 1,
                                                       None if idx not in role_map.keys() else role_map[idx])
        # for idx in role_map:
        #     self._teammates[idx] = AgentPerspective(idx, my_index, self._sentences_container,
        #                                                None if idx not in role_map.keys() else role_map[idx])

        # TODO - This is the model that will be implemented.
        self._model = None

    def update(self, diff_data, request):
        """
        Given the diff_data received in the agent's update function update the perspective of the agent.
        :param diff_data:
        :return:
        """
        for i in range(len(diff_data.index)):
            curr_index = diff_data.loc[i, 'agent']

            if curr_index in self._perspectives.keys():
                agent_sentence = diff_data.loc[i, 'text']
                talk_number = diff_data.loc[i, 'idx']
                message_type = MessageType[diff_data.loc[i, 'type'].upper()]
                day = diff_data.loc[i, 'day']

                if agent_sentence not in UNUSEFUL_SENTENCES:
                    parsed_sentence = self._message_parser.process_sentence(agent_sentence, curr_index, day,
                                                                            talk_number)
                if message_type == MessageType.TALK:
                    if agent_sentence not in UNUSEFUL_SENTENCES:
                        self._perspectives[curr_index].update_perspective(parsed_sentence, talk_number,1)
                elif message_type == MessageType.VOTE:
                    self._perspectives[curr_index].update_vote(parsed_sentence)
                elif message_type == MessageType.EXECUTE:
                    self._perspectives[curr_index].update_status(AgentStatus.DEAD_TOWNSFOLK)
                elif message_type == MessageType.DEAD:
                    self._perspectives[curr_index].update_status(AgentStatus.DEAD_WEREWOLVES)
                elif message_type == MessageType.ATTACK_VOTE:
                    self._perspectives[curr_index].update_vote(parsed_sentence)
                elif message_type == MessageType.WHISPER:
                    if agent_sentence not in UNUSEFUL_SENTENCES:
                        self._perspectives[curr_index].update_perspective(parsed_sentence, talk_number)
                elif message_type == MessageType.FINISH:
                    self._perspectives[curr_index].update_real_role(parsed_sentence.role)
                self._perspectives[curr_index].switch_sides(day )
                self._perspectives[curr_index].log_perspective()



from enum import Enum
import random

class AgentStatus(Enum):
    ALIVE = 1
    DEAD_TOWNSFOLK = 2,
    DEAD_WEREWOLVES = 3


class TeamStrategy:
    def __init__(self, agent_idx, my_idx, sentences_container, role=None):
        """
        :param agent_idx: Index of this agent.
        :param my_idx: Index of our agent.
        """
        self._index = agent_idx
        self.my_agent = my_idx
        self._cooperators = {}
        self._noncooperators = {}
        self._admitted_role = None
        self._assind_roles = {}
        self._status = AgentStatus.ALIVE
        # Represent current agent's change to be voted out of the game
        #TODO: implement setter + logic
        self.under_risk_level = 0
        # Messages ordered by day that are directed to me (think these are only inquire and request messages).
        self.messages_to_me = {}
        self._sentences_container = sentences_container

        self.team = []
        self.conflict = []
        self.react = []
        self.next_attack = None

    def dayone(self):
        if self._base_info._wisper[str(self.my_agent)]==1:
            humans = random.choice(self._noncooperators,2,replace=False)
            #"INQUIRE ANY (DAY 1(AGREE ANY))"
            return f"AND (INQUIRE Agent{self.team[0]} (DAY 1(AGREE Agent{humans[0]}))(INQUIRE Agent{self.team[1]} (DAY 1(AGREE Agent{humans[1]})))"
        elif len(self.conflict) > 0:
            return self.resolve_conflict()
        elif len(self.react) > 0:
            return self.anser()
        elif not (self._assind_roles):
            return "INQUIRE ANY (ESTIMATE ANY ANY)"  # ask players to assign rolls
        else:
            return "OVER"

    def resolve_conflict(self):
        prob = self.conflict.pop()
        choosen = self.check_option(prob[0],prob[1])
        return f"BECAUSE (AND({prob[choosen]})({prob[1-choosen]})) (AND({prob[choosen]})(NOT({prob[1-choosen]})))"

    def anser(self):
        anser = "AND"
        for event in self.react:
            anser += f"({event})"
        return anser

    def check_option(self,option1,option2):
        return 0

    def get_best_attak_for_team(self):
        for w in self.team:
            w.under_risk_level
        return 1  #TODO


