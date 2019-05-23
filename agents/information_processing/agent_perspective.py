from agents.information_processing.message_parsing import *
from enum import Enum
from collections import namedtuple
from math import pow
from agents.information_processing.processed_sentence import ProcessedSentence
from agents.logger import Logger
from agents.game_roles import GameRoles


MIN_SEVERITY_VAL = 1
MAX_SEVERITY_VAL = 3

class AgentStatus(Enum):
    ALIVE = 1
    DEAD_TOWNSFOLK = 2,
    DEAD_WEREWOLVES = 3


HOSTILITY_DISCOUNT_FACTOR = 0.9

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

    def __init__(self, index, history):
        self.index = index
        self._hostility_history = history
        Logger.instance.write("Created new Enemy " + str(self.index) + "  initial history: " + str(self._hostility_history))
        self._total_hostility = 0.0
        self._was_updated = False

    def update_hostility(self, hostility, message):
        Logger.instance.write("Logging hostility for agent: " + str(self.index) + "  current history: " + str(self._hostility_history))
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
                    self._total_hostility += pow(HOSTILITY_DISCOUNT_FACTOR, distance) * message_hostility.hostility
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
        return "Enemy index: " + str(self.index) + "  total hostility " + str(self._total_hostility) + " HISTORY: " + \
            str(self._hostility_history)


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
    TODO- If it's easier to be hostile, should everyone start as cooperator.
    """

    def __init__(self, agent_idx, my_idx, sentences_container, player_perspective, role=None):
        """
        :param agent_idx: Index of this agent.
        :param my_idx: Index of our agent.
        :param sentences_container Container that maps talk number to a processed sentence.
        :param player_perspective
        :param role Role of the player if we know it from the role_map.
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
        self._vote_score = 0
        # Messages ordered by day that are directed to me (think these are only inquire and request messages).
        self.messages_to_me = {}
        self._sentences_container = sentences_container
        self._player_perspective = player_perspective

    def get_index(self):
        return self._index

    def update_status(self, status):
        self._status = status

    def update_real_role(self, role):
        self._role = role

    def get_admitted_role(self):
        return self._admitted_role

    def get_messages_to_me(self, day):
        """
        Get messages that were directed to my agent on a given day.
        :param day:
        :return:
        """
        return self.messages_to_me[day]

    def update_non_cooperator(self, message, hostility=1):
        processed = ProcessedSentence(message, hostility, True)
        if hostility < 0:
            Logger.instance.write("Enemy with index " + str(message.target) + " turned into a cooperator.")
            return self.update_cooperator(message, fondness=-hostility)
        non_cooperator = Enemy(message.target, {})
        non_cooperator.update_hostility(hostility, message)
        if message.target in self._cooperators.keys():
            # In a case of a cooperator shown as non cooperator give it a fine in fondness.
            # If fondness turns out negative he will turn into an enemy.
            self._cooperators[message.target].update_fondness(-hostility, message)
        else:
            if message.target not in self._noncooperators.keys():
                Logger.instance.write("[AGENT " + str(self._index) + "]: Adding a new enemy: " + str(message.target) + \
                                      " based on message: " + str(message))
                self._noncooperators[message.target] = non_cooperator
            else:
                # Update the hostility.
                Logger.instance.write("[AGENT " + str(self._index) + "]: Updating existing enemy: " + str(message.target)
                                      + " based on message " + str(message))
                self._noncooperators[message.target].update_hostility(hostility, message)
        return [processed]

    def update_cooperator(self, message, fondness=1):
        processed = ProcessedSentence(message, fondness, False)
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
        return [processed]

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
                Logger.instance.write("Agent " + str(index) + " switch sides! Cooperator to enemy.")
                self._noncooperators[index] = self._cooperators[index].convert_to_enemy()
                self._cooperators.pop(index, None)

        for index, enemy in self._noncooperators.items():
            total_hostility = self._noncooperators[index].get_hostility(day)
            if total_hostility <= 0:
                Logger.instance.write("Agent " + str(index) + " switched sides! Enemy to cooperator.")
                self._cooperators[index] = self._noncooperators[index].convert_to_cooperator()
                self._noncooperators.pop(index, None)

    def update_admitted_role(self, message):
        """
        Update the role of this agent if he admitted to a new role based on a given sentence.
        :param message:
        :return:
        """
        self._admitted_role = {"role": message.role, "reason": message}
        return ProcessedSentence.empty_sentence(message)

    def add_message_directed_to_me(self, message):
        """
        Save messages such as requests or inquires which are directed towards our agent.
        In the case of a request the subject requires from the target to act according to the request.
        In the case of inquire if there is no mention of ANY the subject only wants to know whether the
        target agrees or not, if there is ANY we expect the target to replace the ANY with his answers.
        :param message:
        :return:
        """
        if message.day in self.messages_to_me.keys():
            self.messages_to_me[message.day].append(message)
        else:
            self.messages_to_me[message.day] = [message]

    def update_based_on_request(self, message, talk_number):
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
        :param talk_number
        :return:
        """
        content = message.content

        if message.target != "ANY":
            # If there is a request towards someone we will see it as a sign of cooperation.
            self.update_cooperator(message, fondness=2)

        if message.target == self.my_agent:
            self.add_message_directed_to_me(message)

        if content.type == SentenceType.ESTIMATE or content.type == SentenceType.COMINGOUT:
            if GameRoles[content.role] == GameRoles.WEREWOLF or GameRoles[content.role] == GameRoles.POSSESSED:
                hostility = 2 if message.target == "ANY" else 1
                result = self.update_non_cooperator(content, hostility=hostility)
            else:
                fondness = 3 if message.target == "ANY" else 1
                result = self.update_cooperator(content, fondness=fondness)

            self._player_perspective.msg_event(content, talk_number)

        elif content.type == SentenceType.AGREE or content.type == SentenceType.DISAGREE:
            scale = 4 if message.target == "ANY" else 2
            result = self.update_based_on_opinion(content, scale=scale)
        elif content.type == SentenceType.VOTE:
            hostility = 4 if message.target == "ANY" else 1.5
            result = self.update_non_cooperator(content, hostility=hostility)
            self._player_perspective.msg_event(content, talk_number)
        elif content.type == SentenceType.DIVINE:
            hostility = 0.5 if message.target == "ANY" else 0.25
            result = self.update_non_cooperator(content, hostility=hostility)
        elif content.type == SentenceType.GUARD:
            fondness = 3 if message.target == "ANY" else 1
            result = self.update_cooperator(message, fondness)
        elif content.type == SentenceType.XOR:
            result = self.update_based_on_xor(message, talk_number)
        elif content.type == SentenceType.OR:
            result = self.update_based_on_or(message, talk_number)
        elif content.type == SentenceType.ATTACK or content.type == SentenceType.IDENTIFIED:
            # TODO - Unsure if it's needed only used between werewolves, it's obvious they are cooperators.
            pass
        return result

    def update_based_on_or(self, message, talk_number, reason=None):
        """
        Update based on given or message, current naive implementation updates based on each sentence with lower scale
        of fondness or hostility.
        TODO - Look at the most likely sentence based on my agent's perspective and scale the hostility or fondness
        based on the probabilities that my agent gives to one of these events happening based on his perspective.
        :param message:
        :param talk_number
        :return:
        """
        scale = len(message.sentences)
        result = None
        for sentence in message.sentences:
            sentence._replace(reason=reason)
            self.update_perspective(sentence, talk_number, scale=scale)
        return result

    def update_based_on_xor(self, message, talk_number, reason=None):
        """
        Currently a xor message will be processed as two separate messages with lower scale for fondness or
        hostility of these messages because only one of them is true.
        TODO- We would maybe like to check resolvement of xor messages.
        :param message:
        :param talk_number
        :return:
        """
        return self.update_based_on_or(message, talk_number, reason)

    def reprocess_sentences(self, sentences, in_hostility, in_fondness):
        """
        Reprocess sentences that were already processed.
        :param sentences:
        :param in_hostility: Method that will be used to update hostility depends on whether our opinion shows
        agreement or disagreement.
        :param in_fondness: Method that will be used to update fondness depends on whether our opinion shows
        agreement or disagreement.
        :return:
        """
        for sentence in sentences:
            if sentence.is_hostile:
                in_hostility(sentence.sentence, sentence.amount)
            else:
                in_fondness(sentence.sentence, sentence.amount)

    def update_based_on_opinion(self, message, talk_number, scale=2):
        """
        Update the hostility or fondness of an agent based on a given opinion.
        TODO- There is more to it than AGREE= Like and Disagree=Dislike.
        :param message:
        :param talk_number
        :param scale: Controls the amount of hostility or fondness, if an agent requests from everybody to agree
        with the statement of the other agent it means that he supports him much highly then a single agreement.
        :return:
        """
        result = None
        if message.type == SentenceType.AGREE:
            result = self.update_cooperator(message.referencedSentence, fondness=scale)
            in_hostility = self.update_non_cooperator
            in_fondness = self.update_cooperator
        elif message.type == SentenceType.DISAGREE:
            result = self.update_non_cooperator(message.referencedSentence, hostility=scale)
            in_hostility = self.update_cooperator
            in_fondness = self.update_non_cooperator
        processed_sentences = self._sentences_container.get_sentence(talk_number)
        self.reprocess_sentences(processed_sentences, in_hostility, in_fondness)
        self._player_perspective.msg_event(message, talk_number)
        return result

    def update_because_sentence(self, message, talk_number, scale=1):
        """
        Given a because sentence update the cooperators and enemies of this agent.
        Examples of because sentences that shows non cooperation:
        1. Because that x happened I will vote for agent 1.

        Examples for because sentences that show cooperation/
        1. Because that x happened I request anyone to guard agent 1 because he is valuable to the team.
        :param message:
        :param talk_number
        :param scale
        :return:
        """
        cause, effect = message.sentences
        effect._replace(reason=cause)
        result = None

        if effect.type == SentenceType.VOTE:
            result = self.update_non_cooperator(effect, hostility=2 / scale)
            self._player_perspective.msg_event(effect, talk_number)
        elif effect.type == SentenceType.DIVINE:
            result = self.update_non_cooperator(effect, hostility=1 / scale)
        elif effect.type == SentenceType.GUARD:
            result = self.update_cooperator(effect, fondness=1 / scale)
        elif effect.type == SentenceType.AGREE or effect.type == SentenceType.DISAGREE:
            result = self.update_based_on_opinion(effect, talk_number, scale=3)
            self._player_perspective.msg_event(effect, talk_number)
        elif effect.type == SentenceType.ESTIMATE or effect.type == SentenceType.COMINGOUT:
            if GameRoles[effect.role] == GameRoles.WEREWOLF or GameRoles[effect.role] == GameRoles.POSSESSED:
                result = self.update_non_cooperator(effect, hostility=4 / scale)
            else:
                # If we estimate someone to not be in the werewolf team there is some fondness to it.
                result = self.update_cooperator(effect, fondness=1 / scale)
            self._player_perspective.msg_event(effect, talk_number)
        elif effect.type == SentenceType.REQUEST:
            result = self.update_based_on_request(effect, talk_number)
        elif effect.type == SentenceType.INQUIRE:
            result = self.update_based_on_inquire(effect)
        elif effect.type == SentenceType.XOR:
            result = self.update_based_on_xor(message, talk_number, cause)
        elif effect.type == SentenceType.OR:
            result = self.update_based_on_or(effect, talk_number, cause)
        elif effect.type == SentenceType.AND:
            self.update_based_on_and(effect, talk_number, cause)

        return result

    def update_based_on_and(self, message, talk_number, reason=None):
        # Process all sentences.
        for sentence in message.sentences:
            sentence._replace(reason=reason)
            self.update_perspective(sentence, talk_number)

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
        return ProcessedSentence.empty_sentence(message)

    def update_perspective(self, message, talk_number, scale=1):
        """
        Given a new message update my perspective.
        :param message:
        :param talk_number
        :param scale Will be higher for sentences that are less likely to be true (for example if this part
        of an or/xor statement or this agent is an avid liar).
        :return:
        """
        result = None
        if message.type == SentenceType.ESTIMATE or message.type == SentenceType.COMINGOUT:
            if message.target == self._index:
                result = self.update_admitted_role(message)
            elif GameRoles[message.role] == GameRoles.WEREWOLF or GameRoles[message.role] == GameRoles.POSSESSED:
                result = self.update_non_cooperator(message, hostility=1 / scale)

            self._player_perspective.msg_event(message, talk_number)

        elif message.type == SentenceType.VOTE:
            result = self.update_non_cooperator(message, hostility=1.5 / scale)
            self._player_perspective.msg_event(message, talk_number)

        elif message.type == SentenceType.REQUEST:
            result = self.update_based_on_request(message, talk_number)
        elif message.type == SentenceType.INQUIRE:
            result = self.update_based_on_inquire(message)
        elif message.type == SentenceType.BECAUSE:
            result = self.update_because_sentence(message, talk_number)
        elif message.type == SentenceType.AGREE or message.type == SentenceType.DISAGREE:
            result = self.update_based_on_opinion(message, talk_number)
        elif message.type == SentenceType.XOR:
            result = self.update_based_on_xor(message, talk_number)
        elif message.type == SentenceType.OR:
            result = self.update_based_on_or(message,  talk_number)
        elif message.type == SentenceType.NOT:
            self.update_based_on_not(message, talk_number)
        elif message.type == SentenceType.AGREE or message.type == SentenceType.DISAGREE:
            result = self.update_based_on_opinion(message, talk_number, scale)

        if result is not None:
            self._sentences_container.add_sentence(talk_number, result)

    def update_based_on_not(self, message, talk_number):
        """
        Update based on negation sentence. Go over all the negated sentences and update the perspective using a
        negative scale. That way the sentence will get the exact opposite effect, if the original sentence shows
        hostility negating it will result as a sign of fondness and same vv.
        :param message:
        :param talk_number
        :return:
        """
        for sentence in message.sentences:
            self.update_perspective(sentence, talk_number, scale=-1)

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
        Logger.instance.write("Logging perspective of agent: " + str(self._index))
        for idx, cooperator in self._cooperators.items():
            Logger.instance.write(str(cooperator))

        for idx, enemy in self._noncooperators.items():
            Logger.instance.write(str(enemy))

    def update_vote_score(self, value):
        if abs(value) < MIN_SEVERITY_VAL or abs(value) > MAX_SEVERITY_VAL:
            assert "Vote score value is out of bound"
        self._vote_score += value
