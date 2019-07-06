from agents.states.agent_state import NightAgentState
from agents.tasks.task_type import TaskType
from agents.states.state_type import StateType
import random

BASE_STATE_PROB = 0.5

class Night_one(NightAgentState):
    """
    State of the agent in the first day of the game. He has no info so he will
    select agents randomly and asked them questions.
    Once he asked enough/ got no replies at all answer with "Over" or "Skip".
    """

    def get_type(self):
        return StateType.NIGHT_ONE

    def __init__(self, my_agent, agent_indices):
        NightAgentState.__init__(self, my_agent, agent_indices)

    def get_task_mask(self):
        """
        In the first day we ignore tasks completely.
        :return:
        """
        return {val: 1 for val in list(TaskType)}

    def talk(self, task_manager):
        """
        In the talk function in the first day we ask random questions.
        :return:
        """
        if task_manager.num_tasks() > 0:
            return task_manager.get_most_important_task().handle_task()
        return ""





