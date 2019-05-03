from .message_parsing import *
import random
from enum import Enum
from collections import namedtuple
from math import pow


class AgentStatus(Enum):
    ALIVE = 1
    DEAD_TOWNSFOLK = 2,
    DEAD_WEREWOLVES = 3


HOSTILITY_DISCOUNT_FACOTR = 0.9

FONDNESS_DISCOUNT_FACTOR = 0.9

MessageHostility = namedtuple("MessageHostility", "message hostility")

MessageFondness = namedtuple("MessageFondness", "message fondness")


class Enemy(object):
    """
    Represent non-cooperators of this player, if there is no cooperation we will hold the index of the
    non-cooperator and the type of the message that was used to create this enemy,
    An enemy can be created using the following examples:
    1. He blamed the target to be a werewolf or possessed.
    2. He voted against him.
    3. He told people to vote against him.
    etc.
    We will put certain weights of the hostility of this agent towards the enemy because there are certain levels to
    it.
    The hostility level will be discounted based on the number of days that have passed since it was last seen.
    """

    def __init__(self, index, history={}):
        self.index = index
        self._hostility_history = history
        self._total_hostility = 0.0
        self._was_updated = False

    def update_hostility(self, hostility, message):
        message_hostility = MessageHostility(message, hostility)
        if message.day in self._hostility_history.keys():
            self._hostility_history[message.day].append(message_hostility)
        else:
            self._hostility_history[message.day] = [message_hostility]

        self._was_updated = True

    def get_hostility(self, current_day):
        """
        Compute the total hostility based on  a discounted sum.
        :return:
        """
        if not self._was_updated:
            return self._total_hostility
        else:
            self._total_hostility = 0.0
            for day, message_hostilities in self._hostility_history.items():
                distance = current_day - day
                for message_hostility in message_hostilities:
                    self._total_hostility += pow(HOSTILITY_DISCOUNT_FACOTR, distance) * message_hostility.hostility
            self._was_updated = False
            return self._total_hostility

    def convert_to_cooperator(self):
        """
        Change the sign of each value of hostility in the history and return a cooperator
        with the given history.
        :return:
        """
        fondness_history = {}
        for day in self._hostility_history.keys():
            fondness_history[day] = []
            for message_hostility in self._hostility_history[day]:
                fondness_history[day].append(MessageFondness(message_hostility.message, -message_hostility.hostility))
        return Cooperator(self.index, fondness_history)

    def __eq__(self, other):
        return self.index == other.index

    def __str__(self):
        return "Enemy index: " + str(self.index) + "  total hostility " + str(self._total_hostility)


class Cooperator(object):
    """
    Defines a cooperator that we have throughout the game. This is defined by several events that we find
    throughout the game. Examples are:
    1. This agent required to bodyguard to guard this agent.
    2. The agent shows agreement based on talk number from the past.

    Same as an enemy there are levels of cooperation which we will call fondness. For example an agreement doesn't
    show the same level of fondness as requesting everyone to agree with a given statement.
    """

    def __init__(self, index, history={}):
        self.index = index
        self._fondness_history = history
        self._was_updated = False
        self._total_fondness = 0.0

    def update_fondness(self, fondness, message):
        message_fondness = MessageFondness(message, fondness)
        if message.day in self._fondness_history.keys():
            self._fondness_history[message.day].append(message_fondness)
        else:
            self._fondness_history[message.day] = [message_fondness]
        self._was_updated = True

    def get_fondness(self, current_day):
        if not self._was_updated:
            return self._total_fondness
        else:
            self._total_fondness = 0.0
            for day, messages_fondness in self._fondness_history.items():
                distance = current_day - day
                for message_fondness in messages_fondness:
                    self._total_fondness += pow(FONDNESS_DISCOUNT_FACTOR, distance) * message_fondness.fondness
            self._was_updated = False
            return self._total_fondness

    def __eq__(self, other):
        return self.index == other.index

    def convert_to_enemy(self):
        hostility_history = {}
        for day in self._fondness_history.keys():
            hostility_history[day] = []
            for message_fondness in self._fondness_history[day]:
                hostility_history[day].append(MessageHostility(message_fondness.message, -message_fondness.fondness))
        return Enemy(self.index, hostility_history)

    def __str__(self):
        return "Cooperator index: " + str(self.index) + "  total fondness " + str(self._total_fondness)


class AgentPerspective(object):
    """
    Contains information about specific agent in the game.
    Agent Index: Index of this agents.
    Liar Score: Based on information given throughout the game a score whether this agent
    is a truth teller or a liar.
    Admitted role: Role that the agent stated that he has, paired with the sentence in which he said he has
    that role.
    Likely cooperators: The agents that are likely to cooperate with this agent.
    Likely non-cooperators: The agents that this agent doesn't cooperate with, he showed disagreement to them.
    Likely Role: The role I think that player has based on what happened thus far.
    Status: Status of the agent, is he alive or dead, if he is dead, who killed him? The townsfolk or the
    werewolves.
    """

    def __init__(self, agent_idx, my_idx, role=None):
        """
        :param agent_idx: Index of this agent.
        :param my_idx: Index of our agent.
        """
        self._index = agent_idx
        self.my_agent = my_idx
        self._liar_score = 0.0
        self._cooperators = {}
        self._noncooperators = {}
        self._admitted_role = None
        self._likely_role = None
        self._status = AgentStatus.ALIVE
        self._role = role

        # Messages ordered by day that are directed to me (think these are only inquire and request messages).
        self.messages_to_me = {}

    def update_status(self, status):
        self._status = status

    def update_real_role(self, role):
        self._role = role

    def get_messages_to_me(self, day):
        """
        Get messages that were directed to my agent on a given day.
        :param day:
        :return:
        """
        return self.messages_to_me[day]

    def update_non_cooperator(self, message, hostility=1):
        if hostility < 0:
            return self.update_cooperator(message, fondness=-hostility)
        non_cooperator = Enemy(message.target)
        non_cooperator.update_hostility(hostility, message)
        if message.target in self._cooperators.keys():
            # In a case of a cooperator shown as non cooperator give it a fine in fondness.
            # If fondness turns out negative he will turn into an enemy.
            self._cooperators[message.target].update_fondness(-hostility, message)
        else:
            if message.target not in self._noncooperators.keys():
                self._noncooperators[message.target] = non_cooperator
            else:
                # Update the hostility.
                self._noncooperators[message.target].update_hostility(hostility, message)

    def update_cooperator(self, message, fondness=1):
        if fondness < 0:
            self.update_non_cooperator(message, hostility=-fondness)
        cooperator = Cooperator(message.target)
        cooperator.update_fondness(fondness, message)
        if message.target in self._noncooperators.keys():
            self._noncooperators[message.target].update_hostility(-fondness, message)

        else:
            if message.target not in self._cooperators.keys():
                self._cooperators[message.target] = cooperator
            else:
                self._cooperators[message.target].update_fondness(message)

    def switch_sides(self, day):
        """
        Go over all the cooperators and non cooperators and check if all of them have a positive value of
        fondness of hostility. If one of them has a negative value it means that it switched sides.
        :param day
        :return:
        """
        for index, cooperator in self._cooperators.items():
            total_fondness = self._cooperators[index].get_fondness(day)
            if total_fondness <= 0:
                print("Agent " + str(index) + " switch sides! Cooperator to enemy.")
                self._noncooperators[index] = self._cooperators[index].convert_to_enemy()
                self._cooperators.pop(index, None)

        for index, enemy in self._noncooperators.items():
            total_hostility = self._noncooperators[index].get_hostility(day)
            if total_hostility <= 0:
                print("Agent " + str(index) + " switched sides! Enemy to cooperator.")
                self._cooperators[index] = self._noncooperators[index].convert_to_cooperator()
                self._noncooperators.pop(index, None)

    def update_admitted_role(self, message):
        """
        Update the role of this agent if he admitted to a new role based on a given sentence.
        :param message:
        :return:
        """
        self._admitted_role = {"role": message.role, "reason": message}

    def add_message_directed_to_me(self, message):
        if message.day in self.messages_to_me.keys():
            self.messages_to_me[message.day].append(message)
        else:
            self.messages_to_me[message.day] = [message]

    def update_based_on_request(self, message):
        """
        Update the perspective of this agent based on the given request.
        There are a lot of ways we can interpret a given request:
        1. If the request is from everyone (ANY) and it contains an estimate or knowledge sentence it's a direct
        blow against the target of this sentence, showing that this agent sees the target as it's enemy.
        2. In the case of requests of given actions that are actions that show cooperation like guarding and there
        are actions that show that this agent thinks of the target as an enemy like: divination, vote and attack (even
        though attack is only necessary for werewolves in the night phase).
        For each message give an increased hostility if it is hostile and the request is from everybody (ANY).
        :param message:
        :return:
        """
        content = message.content
        if message.target == self.my_agent:
            self.add_message_directed_to_me(message)

        if content.type == SentenceType.ESTIMATE or content.type == SentenceType.COMINGOUT:
            if GameRoles[content.role] == GameRoles.WEREWOLF or GameRoles[content.role] == GameRoles.POSSESSED:
                hostility = 2 if message.target == "ANY" else 1
                self.update_non_cooperator(content, hostility=hostility)
            else:
                fondness = 3 if message.target == "ANY" else 1
                self.update_cooperator(content, fondness= fondness)

        elif content.type == SentenceType.AGREE or content.type == SentenceType.DISAGREE:
            scale = 4 if message.target == "ANY" else 2
            self.update_based_on_opinion(content, scale=scale)
        elif content.type == SentenceType.VOTE:
            hostility = 4 if message.target == "ANY" else 1.5
            self.update_non_cooperator(content, hostility=hostility)
        elif content.type == SentenceType.DIVINE:
            hostility = 0.5 if message.target == "ANY" else 0.25
            self.update_non_cooperator(content, hostility=hostility)
        elif content.type == SentenceType.GUARD:
            fondness = 3 if message.target == "ANY" else 1
            self.update_cooperator(message, fondness)
        elif content.type == SentenceType.XOR:
            self.update_based_on_xor(message)
        elif content.type == SentenceType.OR:
            self.update_based_on_or(message)
        elif content.type == SentenceType.ATTACK or content.type == SentenceType.IDENTIFIED:
            # TODO - Unsure if it's needed only used between werewolves, it's obvious they are cooperators.
            pass

    def update_based_on_or(self, message):
        """
        Update based on given or message, current naive implementation updates based on each sentence with lower scale
        of fondness or hostility.
        TODO - Look at the most likely sentence based on my agent's perspective and scale the hostility or fondness
        based on the probabilities that my agent gives to one of these events happening based on his perspective.
        :param message:
        :return:
        """
        scale = len(message.sentences)
        for sentence in message.sentences:
            self.update_perspective(sentence, scale=scale)

    def update_based_on_xor(self, message):
        """
        Currently a xor message will be processed as two separate messages with lower scale for fondness or
        hostility of these messages because only one of them is true.
        TODO- We would maybe like to check resolvement of xor messages.
        :param message:
        :return:
        """
        self.update_based_on_or(message)

    def update_based_on_opinion(self, message, scale=2):
        """
        Update the hostility or fondness of an agent based on a given opinion.
        TODO- There is more to it than AGREE= Like and Disagree=Dislike.
        :param message:
        :param scale: Controls the amount of hostility or fondness, if an agent requests from everybody to agree
        with the statement of the other agent it means that he supports him much highly then a single agreement.
        :return:
        """
        if message.type == SentenceType.AGREE:
            self.update_cooperator(message.referencedSentence, fondness=scale)
        elif message.type == SentenceType.DISAGREE:
            self.update_non_cooperator(message.referencedSentence, hostility=scale)

    def update_because_sentence(self, message, scale=1):
        """
        Given a because sentence update the cooperators and enemies of this agent.
        Examples of because sentences that shows non cooperation:
        1. Because that x happened I will vote for agent 1.

        Examples for because sentences that show cooperation/
        1. Because that x happened I request anyone to guard agent 1 because he is valuable to the team.
        :param message:
        :param scale
        :return:
        """
        cause, effect = message.sentences
        effect._replace(reason=cause)

        if effect.type == SentenceType.VOTE:
            self.update_non_cooperator(effect, hostility=3 / scale)
        elif effect.type == SentenceType.DIVINE:
            self.update_non_cooperator(effect, hostility=1 / scale)
        elif effect.type == SentenceType.GUARD:
            self.update_cooperator(effect, fondness=1 / scale)
        elif effect.type == SentenceType.AGREE or effect.type == SentenceType.DISAGREE:
            self.update_based_on_opinion(effect, scale=3)
        elif effect.type == SentenceType.ESTIMATE or effect.type == SentenceType.COMINGOUT:
            if GameRoles[effect.role] == GameRoles.WEREWOLF or GameRoles[effect.role] == GameRoles.POSSESSED:
                self.update_non_cooperator(effect, hostility=2 / scale)
            else:
                # If we estimate someone to not be in the werewolf team there is some fondness to it.
                self.update_cooperator(effect, fondness=1 / scale)
        elif effect.type == SentenceType.REQUEST:
            self.update_based_on_request(effect)
        elif effect.type == SentenceType.INQUIRE:
            self.update_based_on_inquire(effect)
        elif effect.type == SentenceType.XOR:
            self.update_based_on_xor(message)
        elif effect.type == SentenceType.OR:
            self.update_based_on_or(effect)
        elif effect.type == SentenceType.AND:
            # Process all sentences.
            for sentence in effect.sentences:
                sentence._replace(reason=cause)
                self.update_perspective(sentence)

    def update_based_on_inquire(self, message):
        """
        Update the cooperators and enemies of this agent based on inquires that he sent throughout the game.
        TODO- Does asking questions mean anything about the relationship between two agents?
        :param message:
        :return:
        """
        # Save inquires that are directed to our agent. Maybe we will answer.
        if message.target == self.my_agent:
            self.add_message_directed_to_me(message)

    def update_perspective(self, message, scale=1):
        """
        Given a new message update my perspective.
        :param message:
        :param scale Will be higher for sentences that are less likely to be true (for example if this part
        of an or/xor statement or this agent is an avid liar).
        :return:
        """
        if message.type == SentenceType.ESTIMATE or message.type == SentenceType.COMINGOUT:
            if message.target == self._index:
                self.update_admitted_role(message)
            elif GameRoles[message.role] == GameRoles.WEREWOLF or GameRoles[message.role] == GameRoles.POSSESSED:
                self.update_non_cooperator(message, hostility=1 / scale)

        elif message.type == SentenceType.VOTE:
            self.update_non_cooperator(message, hostility=1.5 / scale)
        elif message.type == SentenceType.REQUEST:
            self.update_based_on_request(message)
        elif message.type == SentenceType.INQUIRE:
            self.update_based_on_inquire(message)
        elif message.type == SentenceType.BECAUSE:
            self.update_because_sentence(message)
        elif message.type == SentenceType.AGREE or message.type == SentenceType.DISAGREE:
            self.update_based_on_opinion(message)
        elif message.type == SentenceType.XOR:
            self.update_based_on_xor(message)
        elif message.type == SentenceType.OR:
            self.update_based_on_or(message)

    def update_based_on_not(self, message):
        """
        Update based on negation sentence. Go over all the negated sentences and update the perspective using a
        negative scale. That way the sentence will get the exact opposite effect, if the original sentence shows
        hostility negating it will result as a sign of fondness and same vv.
        :param message:
        :return:
        """
        for sentence in message.sentences:
            self.update_perspective(sentence, scale=-1)

    def update_vote(self, vote):
        """
        Update cooperators and enemies based on vote of the agent. A vote will get a high value
        of hostility because it means this agent wants the  other one dead.
        :param vote:
        :return:
        """
        self.update_non_cooperator(vote, hostility=4)

    def lie_detected(self):
        """
        In case a lie was detected we will increment the liar score of this agent, it is more likely that
        he is a liar.
        :return:
        """
        self._liar_score += 1

    def log_perspective(self):
        print("Logging perspective of agent: ", self._index)
        for idx, cooperator in self._cooperators.items():
            print(cooperator)

        for idx, enemy in self._noncooperators.items():
            print(enemy)

