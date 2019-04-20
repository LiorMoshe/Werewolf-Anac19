from .message_parsing import *
from enum import Enum

class MessageType(Enum):
    TALK = 1,
    VOTE = 2


# These sentences currently, don't help us much (maybe will be used in future dev).
UNUSEFUL_SENTENCES = ['Skip', 'Over']


class AgentBelief(object):
    """
    This class will hold our belief of the intentions and goals of the agent
    of the given index, this will help our agent make decisions throughout the game.
    """

    def __init__(self, index):
        self._index = index
        self._agent_role = None

        # The agents status, either dead or alive.
        self._agent_status = "ALIVE"

        # Map the actions done by the agent on given days/ talk number (TBD)
        self._agent_actions = {}

        # Holds estimations of this agent over other agents roles, who he ESTIMATED.
        self._agent_estimations = {}

        # Holds knowledge of agent over other agents roles, who he said is COMINGOUT.
        self._agent_knowledge = {}

        # What does the agent object to. TODO- Check if negations of sentences is possible.
        self._agent_objections = {}

        # All of the agents requests, mapped by day.
        self._agent_requests = {}

        # All of the agents inquires, mapped by day.
        self._agents_inquires = {}

        # All the agents votes, mapped by day.
        self._agent_votes = {}

        # Pairs of messages such that if one is true the other is false and vv.
        self._agent_xor_messages = {}

    def save_message_based_on_type(self, message, talk_number):
        """
        Save a given message in one of our dictionaries based on it's type, messages differ in that
        they can show intents,requests, questions and votes of the agent.
        :param message:
        :param talk_number
        :return:
        """
        if message.type in KNOWLEDGE:
            self._agent_knowledge[talk_number] = message
        elif message.type in ACTIONS:
            self.add_new_action(message, talk_number)
        elif message.type in ACTION_RESULT:
            self.add_new_action_result(message, talk_number)
        elif message.type == SentenceType.REQUEST:
            self._agent_requests[talk_number] = message
        elif message.type == SentenceType.INQUIRE:
            self._agents_inquires[talk_number] = message
        elif message.type == SentenceType.BECAUSE:
            self.process_cause_and_effect(message, talk_number)
        elif message.type == SentenceType.AND:
            self._agent_knowledge[talk_number] = message.sentences
        elif message.type == SentenceType.OR:
            pass
        elif message.type == SentenceType.XOR:
            self._agent_xor_messages[talk_number] = (message.sentences[0],  message.sentences[1])
        elif message.type == SentenceType.NOT:
            self._agent_objections[talk_number] = message

    def update_belief(self, diff_data, message_type=MessageType.TALK):
        """
        Update our belief of this agents actions, we will get all the data that was sent
        before the agent talked (meaning all the rows in the original diff_data dataframe that were before
        the row that showed what this agent said).
        TODO- Currently we will model the agents belief in a shallow manner, no nested structure (we don't take into
        account how he reacts to other agents messages, just react to what he thinks).
        :param diff_data: Pandas dataframe that represents what happened since we last talked until this agent
        talked.
        :param message_type
        :return: None
        """
        # Currently we will only look at the sentence of this agent.
        agent_sentence = diff_data.loc[len(diff_data.index) - 1, 'text']
        talk_number = 0
        print("MESSAGE TYPE: ", message_type)

        if message_type == MessageType.TALK:
            if agent_sentence not in UNUSEFUL_SENTENCES:
                parsed_sentence = process_sentence(agent_sentence, self._index)
                print("PARSED: ", parsed_sentence)
                # if parsed_sentence.type in KNOWLEDGE:
                #     self._agent_knowledge[talk_number] = parsed_sentence
                # elif parsed_sentence.type in ACTIONS:
                #     self.add_new_action(parsed_sentence, talk_number)
                # elif parsed_sentence.type in ACTION_RESULT:
                #     self.add_new_action_result(parsed_sentence, talk_number)
                # elif parsed_sentence.type == SentenceType.REQUEST:
                #     self._agent_requests[talk_number] = parsed_sentence
                # elif parsed_sentence.type == SentenceType.INQUIRE:
                #     self._agents_inquires[talk_number] = parsed_sentence
                # elif parsed_sentence.type == SentenceType.BECAUSE:

        elif message_type == MessageType.VOTE:
            self.add_new_vote(agent_sentence, talk_number)

    def add_new_vote(self, sentence, talk_number):
        parsed_message = process_sentence(sentence, self._index)
        self._agent_votes[talk_number] = parsed_message

    def process_cause_and_effect(self, parsed_sentence, talk_number):
        """
        Parse sentence of cause and effect type the cause will be appended to knowledge of the agent
        and effect will be added based on it's type.
        TODO - This function relies on that BECAUSE type only holds two sentences the cause and the effect.
        :param parsed_sentence:
        :return:
        """
        cause, effect = parsed_sentence.sentences
        effect.reason = cause
        self.save_message_based_on_type(effect, talk_number)
        self.save_message_based_on_type(cause, talk_number)


    def add_new_action(self, action, talk_number):
        """
        TODO- Unsure if this is necessary
        :param action:
        :param talk_number:
        :return:
        """

        if action.type == SentenceType.VOTE:
            # If this is a vote action we will fill this information with no reason for the vote.
            self._agent_votes[talk_number] = Vote(action.target, None)

    def add_new_action_result(self, action_result, talk_number):
        if action_result.type == SentenceType.VOTED:
            self._agent_votes[talk_number] = Vote(action_result.target, None)
        else:
            self._agent_actions[talk_number] = action_result



