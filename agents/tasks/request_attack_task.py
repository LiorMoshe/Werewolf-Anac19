from agents.tasks.base_task import BaseTask
from agents.tasks.task_type import TaskType
from agents.sentence_generators.logic_generators import *


# If a day has passed and we have survived this is not very urgent to request everyone's votes.
DISCOUNT = 0.5

class RequestAttackTask(BaseTask):
    """
    This task is used when we see there is an agent that is against us and there is no large
    group that dislikes him, we wish to gain traction by requesting agents to vote for him.
    """

    def __init__(self, hater, importance, day, relevant_agents, my_index):
        BaseTask.__init__(self, importance, day, relevant_agents, my_index)
        self._hater = hater

    def update_importance_based_on_day(self, day):
        self._importance *= DISCOUNT * (day - self._day)

    def get_hater(self):
        return self._hater

    def get_type(self):
        return TaskType.REQUEST_ATTACK_TASK

    def handle_task(self, **kwargs):
        return request_sentence("ANY", wrap(attack(self._hater)))