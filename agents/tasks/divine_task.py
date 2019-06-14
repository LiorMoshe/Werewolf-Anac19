from agents.strategies.player_evaluation import PlayerEvaluation
from agents.tasks.base_task import BaseTask
from agents.tasks.task_type import TaskType
from agents.sentence_generators.logic_generators import *

class DivineTask(BaseTask):
    """
    We will use this task if we want the medium that we trust to identify
    a role of agent that was executed or attacked in the game.
    """

    def __init__(self, importance, day, relevant_agents, my_index, seer_idx, target_idx):
        BaseTask.__init__(self, importance, day, relevant_agents, my_index)
        self._seer = seer_idx
        self._target = target_idx

    def update_importance_based_on_day(self, day):
        pass

    def get_type(self):
        return TaskType.DIVINE_TASK

    def handle_task(self, **kwargs):
        return request_sentence(self._seer, wrap(divination(self._target)))

    @staticmethod
    def generate_divine_task(my_index, seer_idx, importance,
                            day):
        target = PlayerEvaluation.instance.get_divine_target()
        return DivineTask(importance, day, [seer_idx, target],  my_index, seer_idx
                          ,target)