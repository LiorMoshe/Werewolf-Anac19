from .message_parsing import *
from enum import Enum
from ..game_roles import GameRoles

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
    WHISPER = 6,
    FINISH = 7,


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

        # Holds knowledge of agent over other agents roles, who he said is COMINGOUT.
        self._agent_knowledge = {}

        # What does the agent object to. TODO- Check if negations of sentences is possible.
        self._agent_objections = {}

        # All of the agents requests, mapped by day.
        self._agent_requests = {}

        # All  of the agents inquires, mapped by day.
        self._agents_inquires = {}

        # All the agents votes, mapped by day.
        self._agent_votes = {}

        # Pairs of messages such that if one is true the other is false and vv.
        self._agent_xor_messages = {}

        # All or messages that this agent has sent.
        self._agent_or_messages = {}

        # When we get a final finish message all agents reveal their true roles.
        self._agent_real_role = None

        # In case it is a werewolf we will receive messages from it during the night phase in the form of whispers.
        self._agent_whispers = {}

        # Indexes of agents that this agent voted against/ agents that he questions.
        self._enemies = {}

        # A role that the agent admitted to be, can't know if it's truth or a lie.
        # Keep the sentence in which he admitted.
        self._agent_admitted_role = {"role": None, "reason": None}

        self._lying_detected = False

        # Probability of the other agents cooperating or oppposing to this agent.
        self._cooperator_probs = {}

    def set_role(self, role):
        self._agent_role = GameRoles[role]

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
            self._agent_or_messages[talk_number] = message
        elif message.type == SentenceType.XOR:
            self._agent_xor_messages[talk_number] = (message.sentences[0],  message.sentences[1])
        elif message.type == SentenceType.NOT:
            self._agent_objections[talk_number] = message

    def update_belief(self, diff_data):
        """
        Update our belief of this agents actions, we will get all the data that was sent
        before the agent talked (meaning all the rows in the original diff_data dataframe that were before
        the row that showed what this agent said).
        TODO- Currently we will model the agents belief in a shallow manner, no nested structure (we don't take into
        account how he reacts to other agents messages, just react to what he thinks).
        :param diff_data: Pandas dataframe that represents what happened since we last talked until this agent
        talked.
        :return: None
        """
        # Currently we will only look at the sentence of this agent.
        agent_sentence = diff_data.loc[len(diff_data.index) - 1, 'text']
        talk_number = diff_data.loc[len(diff_data.index) - 1, 'idx']
        message_type = MessageType[diff_data.loc[len(diff_data.index) - 1, 'type'].upper()]
        day = diff_data.loc[len(diff_data.index) - 1, 'day']

        print("MESSAGE TYPE: ", message_type)
        parsed_sentence = agent_sentence
        if agent_sentence not in UNUSEFUL_SENTENCES:
            parsed_sentence = process_sentence(agent_sentence, self._index)

        if message_type == MessageType.TALK:
            if agent_sentence not in UNUSEFUL_SENTENCES:
                print("Current sentence: ", agent_sentence)
                self.save_message_based_on_type(parsed_sentence, talk_number)
        elif message_type == MessageType.VOTE:
            self.add_public_vote(agent_sentence, day)
        elif message_type == MessageType.EXECUTE:
            self._agent_status = Dead(self._index, Species.HUMANS)
        elif message_type == MessageType.DEAD:
            self._agent_status = Dead(self._index, Species.WEREWOLVES)
        elif message_type == MessageType.ATTACK_VOTE:
            self.add_attack_vote(parsed_sentence, talk_number)
        elif message_type == MessageType.WHISPER:
            self.add_whisper(parsed_sentence, talk_number)
        elif message_type == MessageType.FINISH:
            self.save_agent_real_role(parsed_sentence)

    def add_knowledge(self, sentences, talk_number):
        """
        Handling the case where the agent says he has some role, we can't be sure that he is saying the truth.
        :param sentences:
        :param talk_number
        :return:
        """
        for sentence in sentences:
            if sentence.type == SentenceType.COMINGOUT:
                if sentence.subject == sentence.target:
                    if self._agent_admitted_role:
                        self._agent_admitted_role.role = GameRoles[sentence.role]
                        self._agent_admitted_role.reason = sentence
                    else:
                        # If the agent is a dumbass and admitted to two roles twice he is a liar.
                        self._lying_detected = False
        if len(sentences) == 1:
            self._agent_knowledge[talk_number] = sentences[0]
        else:
            self._agent_knowledge[talk_number] = sentences

    def get_status(self):
        return self._agent_status

    def get_admitted_role(self):
        return self._agent_admitted_role

    def save_agent_real_role(self, parsed_message):
        """
        In the final finish all agents come out with their real roles. We will save it in the belief
        of the agents in order to see how our belief about the agents matches the reality.
        The expectation is that when the message type is FINISH we will always
        receive a  COMINGOUT message.
        :param parsed_message: Sentence sent from the agent.
        :return:
        """
        self._agent_real_role = GameRoles[parsed_message.role]

    def add_whisper(self, parsed_message, talk_number):
        if self._agent_role is not GameRoles.WEREWOLF:
            self._agent_role = GameRoles.WEREWOLF

        self._agent_whispers[talk_number] = parsed_message

    def add_attack_vote(self, parsed_message, talk_number):
        """
        Given an attack vote by a member of our werewolves group save it in it's actions and update
        the role of this agent to a werewolf (other agents don't have the ability to attack).
        :param parsed_message:
        :param talk_number:
        :return:
        """
        if self._agent_role is not GameRoles.WEREWOLF:
            self._agent_role = GameRoles.WEREWOLF
        self._agent_actions[talk_number] = parsed_message

    def add_public_vote(self, parsed_message, day):
        print("Adding new Vote day: ", day)
        self._agent_votes[day] = parsed_message
        if parsed_message.votedAgainst not in self._enemies:
            self._enemies[parsed_message.votedAgainst] = 1
        else:
            self._enemies[parsed_message.votedAgainst] += 1

    def process_cause_and_effect(self, parsed_sentence, talk_number):
        """
        Parse sentence of cause and effect type the cause will be appended to knowledge of the agent
        and effect will be added based on it's type.
        TODO - This function relies on that BECAUSE type only holds two sentences the cause and the effect.
        :param parsed_sentence:
        :param talk_number
        :return:
        """
        cause, effect = parsed_sentence.sentences
        print("CAUSE: ", cause)
        print("EFFECT: ", effect)
        effect._replace(reason=cause)
        self.save_message_based_on_type(effect, talk_number)
        self.save_message_based_on_type(cause, talk_number)

    def add_new_action(self, action, talk_number):
        """
        TODO- Unsure if this is necessary
        :param action:
        :param talk_number:
        :return:
        """
        self._agent_actions[talk_number] = action

    def add_new_action_result(self, action_result, talk_number):
        if action_result.type == SentenceType.VOTED:
            self._agent_votes[talk_number] = Vote(action_result.target, None)
        else:
            self._agent_actions[talk_number] = action_result



