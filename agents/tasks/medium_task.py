from agents.tasks.base_task import BaseTask
from agents.tasks.task_type import TaskType
from agents.sentence_generators.logic_generators import *
import numpy as np

DISCOUNT = 0.9

IDENTIFIED_PROB = 0.5

class MediumTask(BaseTask):
    """
    With this task the medium can prioritize its knowledge
    """

    def __init__(self, importance, day, relevant_agents, my_index, agent_tuple=None, comingout=False):
        BaseTask.__init__(self, importance, day, relevant_agents, my_index)
        self._agent_tuple = agent_tuple
        self._comingout = comingout

    def update_importance_based_on_day(self, day):
        self._importance *= DISCOUNT * (day - self._day)

    def get_type(self):
        return TaskType.MEDIUM_TASK

    def handle_task(self, **kwargs):
        if (self._comingout):
            return comingout(self.index, "MEDIUM")
        else:
            coin = np.random.rand()

            if (coin > IDENTIFIED_PROB):
                return request_sentence("ALL",
                                wrap(estimate(self._agent_tuple[0], self._agent_tuple[1])))
            else:
                return identified(self._agent_tuple[0], self._agent_tuple[1])