from agents.tasks.base_task import BaseTask
from agents.sentence_generators.logic_generators import *
from agents.tasks.task_type import TaskType

class VoteTask(BaseTask):
    """
    In this task we will state who we will vote for as an answer to questions.
    """

    def __init__(self, importance, day, relevant_agents, my_index, target):
        BaseTask.__init__(self, importance, day, relevant_agents, my_index)
        self._target = target


    def update_importance_based_on_day(self, day):
        pass

    def get_type(self):
        return TaskType.VOTE_TASK

    def handle_task(self, **kwargs):
        return vote(self._target)