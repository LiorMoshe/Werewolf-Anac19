from abc import ABC, abstractmethod

DUMB_HASH_VALUE = 0

class BaseTask(ABC):
    """
    This represents a basic task that will be handles by our agent, each time we notice a major
    info in the game we will create a new task that may be handled by the agent in the future.
    Tasks importance will be updated as days go by as we go further older tasks seem less important.
    If the task relates to an agent which is out of the game we will remove it from our queue
    of tasks.
    """

    def __init__(self, importance, day, relevant_agents, my_index):
        """
        Base constructor of each task
        :param importance: The tasks importance.
        :param day: The day it was created, used for TIME sentences in the protocol which we will use to reflect
        :param relevant_agents Agents relevant to the creation of this task.
        :param my_index: Index of our agent.
        on days that passed by.
        """
        self._importance = importance
        self._day = day
        self.index = my_index
        self._relevant_agents = relevant_agents

        # Global variable, my eyes, what a horror.
        global DUMB_HASH_VALUE
        DUMB_HASH_VALUE += 1
        self._dumb_hash = DUMB_HASH_VALUE

    @abstractmethod
    def handle_task(self, **kwargs):
        """
        This method will return a sentence in which we resolve the task by letting the other agents
        know what we found and what do we think of it.
        :param kwargs:
        :return:
        """
        pass

    def get_importance(self):
        return self._importance

    def __lt__(self, other):
        return self._importance < other.get_importance()

    def __eq__(self, other):
        return self._dumb_hash == other._dumb_hash and self._day == other._day and self.index == other.index \
                and set(self._relevant_agents) == set(other._relevant_agents)

    def __hash__(self):
        """
        We need this object to be a hashable type in order to be able to use it in our priority queue.
        :return:
        """
        return self._dumb_hash

    @abstractmethod
    def get_type(self):
        pass

    @abstractmethod
    def update_importance_based_on_day(self, day):
        """
        Update the importance of the task based on the current day.
        :param day:
        :return:
        """
        pass

    def is_included(self):
        """
        Is our agent included in this task.
        :return:
        """
        return self.index in self._relevant_agents

    def relevant_agents_beside_me(self):
        """
        Get all relevant agents which is not us.
        :return:
        """
        return [idx for idx in self._relevant_agents if idx != self.index]
