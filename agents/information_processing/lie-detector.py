from agents.game_roles import *


class Lie(object):

    def __init__(self, potential_liars, reasons):
        self._potential_liars = potential_liars

    def get_lying_score(self):
        return 1 / len(self._potential_liars)


class LieDetector(object):
    """
    Given a set of agent's perspectives run a series of tests to detect matches that show that at least
    one of the agents is lying. This will help us know the trustworthiness of other agents in the game.
    """

    def __init__(self, agent_indices, role):
        self.role = role
        self._agent_lies = {}
        for idx in agent_indices:
            self._agent_lies[idx] = []

    def test_agents(self, perspectives):
        roles = {}
        for perspective in perspectives:
            admitted_role = perspective.get_admitted_role()
            if admitted_role is not None:
                if admitted_role.role == self.role and self.role in SPECIAL_ROLES:
                    # He admitted to have my role. 100% lying.
                    pass
                elif admitted_role.role in roles.keys():
                    # Agent admitted to have a special role that other agent has. One or both of them are lying.
                    pass
                elif admitted_role.role in SPECIAL_ROLES:
                    roles[admitted_role.role] = perspective.get_index()




