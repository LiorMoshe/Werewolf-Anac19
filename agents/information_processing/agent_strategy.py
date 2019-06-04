from agents.information_processing.agent_perspective import *
from agents.information_processing.message_parsing import *
from agents.information_processing.sentences_container import SentencesContainer
from agents.game_roles import GameRoles
from agents.information_processing.dissection.sentence_dissector import SentenceDissector
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
    DIVINE = 9,
    REQUEST = 10


class TownsFolkStrategy(object):
    """
    This will be  a townsfolk player strategy, we will hold a perspective for all the players in the game.
    In the case of a player of the werewolf group we need to append to this strategy another perspective that
    inspects moves of werewolves teammates through the night and day.
    """

    def __init__(self, agent_indices, my_index, role_map, player_perspective):
        self._perspectives = {}
        self._message_parser = MessageParser()
        self._sentences_container = SentencesContainer()

        # Initialize the singleton sentences dissector.
        SentenceDissector(self._sentences_container, my_index)

        for idx in agent_indices:
            self._perspectives[idx] = AgentPerspective(idx, my_index,
                                                       None if idx not in role_map.keys() else role_map[idx])

        # TODO - This is the model that will be implemented.
        self._model = None

    def update(self, diff_data):
        """
        Given the diff_data received in the agent's update function update the perspective of the agent.
        :param diff_data:
        :return:
        """
        for i in range(len(diff_data.index)):
            curr_index = diff_data.loc[i, 'agent']
            agent_sentence = diff_data.loc[i, 'text']
            idx = diff_data.loc[i, 'idx']
            turn = diff_data.loc[i, 'turn']
            day = diff_data.loc[i, 'day']
            message_type = MessageType[diff_data.loc[i, 'type'].upper()]
            talk_number = TalkNumber(day, turn, idx)

            # only seer and medium players will see
            if message_type == MessageType.DIVINE:
                 print("DIVINE MESSAGE RECEIVED")
                 parsed_sentence = self._message_parser.process_sentence(agent_sentence, curr_index, day,
                                                                        talk_number)
                 # store divined results
                 self.update_divine_result(parsed_sentence.target, parsed_sentence.species)

            if curr_index in self._perspectives.keys():
                if agent_sentence not in UNUSEFUL_SENTENCES:
                    parsed_sentence = self._message_parser.process_sentence(agent_sentence, curr_index, day,
                                                                            talk_number)
                if message_type == MessageType.TALK:
                    if agent_sentence not in UNUSEFUL_SENTENCES:
                        self._perspectives[curr_index].update_perspective(parsed_sentence, talk_number, day)
                elif message_type == MessageType.VOTE:

                    self._perspectives[curr_index].update_vote(parsed_sentence)
                elif message_type == MessageType.EXECUTE:
                    self._perspectives[curr_index].update_status(AgentStatus.DEAD_TOWNSFOLK)
                elif message_type == MessageType.DEAD:
                    self._perspectives[curr_index].update_status(AgentStatus.DEAD_WEREWOLVES)
                elif message_type == MessageType.ATTACK_VOTE:
                    print("Got attack vote when I am in townsfolk, BUG.")
                elif message_type == MessageType.WHISPER:
                    print("Got whisper when I am in townsfolk, BUG.")
                elif message_type == MessageType.FINISH:
                    self._perspectives[curr_index].update_real_role(parsed_sentence.role)
                self._perspectives[curr_index].switch_sides(day )
                self._perspectives[curr_index].log_perspective()