from collections import namedtuple
from agents.logger import Logger

MessageHostility = namedtuple("MessageHostility", "message hostility")

MessageFondness = namedtuple("MessageFondness", "message fondness")

HOSTILITY_DISCOUNT_FACTOR = 0.9

FONDNESS_DISCOUNT_FACTOR = 0.9


class Cooperator(object):
    """
    Defines a cooperator that we have throughout the game. This is defined by several events that we find
    throughout the game. Examples are:
    1. This agent required to bodyguard to guard this agent.
    2. The agent shows agreement based on talk number from the past.

    Same as an enemy there are levels of cooperation which we will call fondness. For example an agreement doesn't
    show the same level of fondness as requesting everyone to agree with a given statement.
    """

    def __init__(self, index, history, initial_fondness = 0.0):
        self.index = index
        self._fondness_history = history
        self._was_updated = False
        self._total_fondness = initial_fondness
        self._initial_fondness = initial_fondness

    def update_fondness(self, fondness, message):
        message_fondness = MessageFondness(message, fondness)
        return self.update(message_fondness)

    def update(self, message_fondness):
        """
        We only apply discounting for messages coming from the players.
        If we update ht
        :param message_fondness:
        :return:
        """

        if message_fondness.message.day in self._fondness_history.keys():
            self._fondness_history[message_fondness.message.day].append(message_fondness)
        else:
            self._fondness_history[message_fondness.message.day] = [message_fondness]
        self._was_updated = True
        return self

    def has_message_fondness(self, message_fondness):
        """
        Given a message fondness check if we have it in our history.
        :param message_fondness:
        :return:
        """
        message = message_fondness.message
        if message.day in self._fondness_history.keys():
            for curr_fondness in self._fondness_history[message_fondness.message.day]:
                curr_message = curr_fondness.message

                if message.type == curr_message.type and message.subject == curr_message.subject \
                        and message.target == curr_message.target:
                    return True

        return False


    def merge_cooperators(self, cooperator):
        """
        Merge two cooperators objects of agent with the same index to a cooperator object
        with merged history and discounted sum of fondness values.
        :return:
        """
        if self.index != cooperator.index:
            raise Exception("Can't merge enemies with different indices: " + str(self.index) + " and " + str(cooperator.index))

        for messages in cooperator.get_history().values():
            for message_fondness in messages:
                if not self.has_message_fondness(message_fondness):
                    self.update(message_fondness)

    def get_history(self):
        return self._fondness_history

    def get_fondness(self, current_day):
        if not self._was_updated:
            return self._total_fondness
        else:
            self._total_fondness = self._initial_fondness
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

    def __init__(self, index, history, initial_hostility = 0.0):
        self.index = index
        self._hostility_history = history
        self._initial_hostility = initial_hostility
        self._total_hostility = initial_hostility
        self._was_updated = False

    def update_hostility(self, hostility, message):
        message_hostility = MessageHostility(message, hostility)
        return self.update(message_hostility)

    def update(self,  message_hostility):
        if message_hostility.message.day in self._hostility_history.keys():
            self._hostility_history[message_hostility.message.day].append(message_hostility)
        else:
            self._hostility_history[message_hostility.message.day] = [message_hostility]

        self._was_updated = True
        return self

    def get_hostility(self, current_day):
        """
        Compute the total hostility based on  a discounted sum.
        :return:
        """
        if not self._was_updated:
            return self._total_hostility
        else:
            self._total_hostility = self._initial_hostility
            for day, message_hostilities in self._hostility_history.items():
                distance = current_day - day
                for message_hostility in message_hostilities:
                    self._total_hostility += pow(HOSTILITY_DISCOUNT_FACTOR, distance) * message_hostility.hostility
            self._was_updated = False
            return self._total_hostility

    def has_message_hostility(self, message_hostility):
        """
        Given a message hostility check if we have it in our history.
        :param message_hostility:
        :return:
        """
        message = message_hostility.message
        if message.day in self._hostility_history.keys():
            for curr_hostility in self._hostility_history[message_hostility.message.day]:
                curr_message = curr_hostility.message

                if message.type == curr_message.type and message.subject == curr_message.subject \
                    and message.target == curr_message.target:
                    return True

        return False

    def get_history(self):
        return self._hostility_history

    def merge_enemies(self, enemy):
        """
        Merge two Enemy objects of agent with the same index to an enemy object
        with merged history and discounted sum of hostility values.
        :return:
        """
        if self.index != enemy.index:
            raise Exception("Can't merge enemies with different indices: " + str(self.index) + " and " + str(enemy.index))


        for message_hostilities in enemy.get_history().values():
            for message_hostility in message_hostilities:
                if not self.has_message_hostility(message_hostility):
                    self.update(message_hostility)

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

    def scale(self, factor):
        """
        Scale all value of hostility of the player by a given factor.
        :param factor:
        :return:
        """
        for day, message_hostilities in self._hostility_history.items():
            for message_hostility in message_hostilities:
                message_hostility._replace(hostility=message_hostility.hostility * factor)
        self._was_updated = True
        return self


    def __eq__(self, other):
        return self.index == other.index

    def __str__(self):
        return "Enemy index: " + str(self.index) + "  total hostility " + str(self._total_hostility) + " HISTORY: " + \
            str(self._hostility_history)
