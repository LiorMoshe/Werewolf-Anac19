from agents.states.agent_state import AgentState

class DayOne(AgentState):
    """
    State of the agent in the first day of the game. He has no info so he will
    select agents randomly and asked them questions.
    Once he asked enough/ got no replies at all answer with "Over" or "Skip".
    """

    def __init__(self, my_agent, agent_indices):
        AgentState.__init__(self, my_agent, agent_indices)

    def talk(self):
        return self.ask_random_question()



