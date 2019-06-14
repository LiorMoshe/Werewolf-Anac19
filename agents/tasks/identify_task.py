from agents.tasks.base_task import BaseTask
from agents.tasks.task_type import TaskType
from agents.sentence_generators.logic_generators import *

class IdentifyTask(BaseTask):
    """
    We will use this task if we want the medium that we trust to identify
    a role of agent that was executed or attacked in the game.
    TODO-  I think the word "IDENTIFY" isn't included in the game protocol, can we request stuff from the medium.
    """

    def __init__(self, importance, day, relevant_agents, my_index, medium_idx, target_idx):
        BaseTask.__init__(self, importance, day, relevant_agents, my_index)
        self._medium = medium_idx
        self._target = target_idx

    def update_importance_based_on_day(self, day):
        pass

    def get_type(self):
        return TaskType.IDENTIFY_TASK

    def handle_task(self, **kwargs):
        return request_sentence(self._medium, wrap(identify(self._target)))