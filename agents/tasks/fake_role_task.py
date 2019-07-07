from agents.tasks.base_task import BaseTask
from agents.tasks.task_type import TaskType
from agents.sentence_generators.logic_generators import *
import numpy as np


# If a day has passed and we have survived this is not very urgent to request everyone's votes.
DISCOUNT = 0.5

class FakeRoleTask(BaseTask):
    """
    This task is used when we see there is an agent that is against us and there is no large
    group that dislikes him, we wish to gain traction by requesting agents to vote for him.
    """

    def __init__(self, hater, importance, day, relevant_agents, my_index,rol,is_enemy=True):
        BaseTask.__init__(self, importance, day, relevant_agents, my_index)
        self.is_enamy = is_enemy
        self._hater = hater
        self.my_role = rol

    def update_importance_based_on_day(self, day):
        self._importance *= DISCOUNT * (day - self._day)

    def get_hater(self):
        return self._hater

    def get_type(self):
        return TaskType.FAKE_ROLE_TASK

    def handle_task(self, **kwargs):
        if self.my_role == GameRoles.MEDIUM:
            if self.is_enamy:
                return identified(self._hater, GameRoles.WEREWOLF)
            return identified(self._hater, "HUMAN")
        elif self.my_role == GameRoles.SEER:
            if self.is_enamy:
                return divined(self._hater, GameRoles.WEREWOLF)
            return divined(self._hater, "HUMAN")