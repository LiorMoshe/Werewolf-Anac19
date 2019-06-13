from agents.states.agent_state import AgentState
from agents.tasks.task_type import TaskType
from agents.states.state_type import StateType
import random

BASE_STATE_PROB = 0.8

class BaseState(AgentState):
    """
    This is the most basic state of an agent in the game. In this state the agent randomizes
    between finishing tasks of high importance or asking random questions. There is no urge to do specific
    tasks in this state so that task mask will give scale 1.0 to every task.
    """

    def get_type(self):
        return StateType.BASE_STATE

    def get_task_mask(self):
        return {val: 1 for val in list(TaskType)}

    def talk(self, task_manager):
        """
        Randomize between task of highest importance or random question.
        :param task_manager:
        :return:
        """
        if task_manager.num_tasks() > 0:
            coin_flip = random.random()
            if coin_flip > BASE_STATE_PROB:
                return self.ask_unique_random_question()
            else:
                return task_manager.get_most_important_task().handle_task()
        else:
            return self.ask_unique_random_question()