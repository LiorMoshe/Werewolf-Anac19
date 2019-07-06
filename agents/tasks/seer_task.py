from agents.tasks.base_task import BaseTask
from agents.tasks.task_type import TaskType
from agents.sentence_generators.logic_generators import *

DISCOUNT = 0.9

class SeerTask(BaseTask):
    """
    With this task the seer can prioritize its knowledge
    """

    def __init__(self, importance, day, relevant_agents, my_index, target=None, prospect=None, comingout=False):
        BaseTask.__init__(self, importance, day, relevant_agents, my_index)
        self._target = target
        self._prospect = prospect
        self._comingout = comingout

    def update_importance_based_on_day(self, day):
        self._importance *= DISCOUNT * (day - self._day)

    def get_type(self):
        return TaskType.SEER_TASK

    def handle_task(self, **kwargs):
        if (self._comingout):
            return comingout(self.index, "SEER")
        else:   
            return request_sentence(self._target,
                                wrap(estimate(self._prospect, "WEREWOLF")))