from agents.states.agent_state import AgentState
from agents.tasks.task_type import TaskType

class DayOne(AgentState):
    """
    State of the agent in the first day of the game. He has no info so he will
    select agents randomly and asked them questions.
    Once he asked enough/ got no replies at all answer with "Over" or "Skip".
    """

    def __init__(self, my_agent, agent_indices):
        AgentState.__init__(self, my_agent, agent_indices)

    def get_task_mask(self):
        """
        In the first day we ignore tasks completely.
        :return:
        """
        return {val: 0 for val in list(TaskType)}

    def talk(self, task_manager):
        """
        In the talk function in the first day we ask random questions.
        :return:
        """
        return self.ask_unique_random_question()



