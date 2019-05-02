from ..game_roles import *
from ..information_processing.agent_belief import AgentBelief
from .lie import Lie


class RuleBasedStrategy(object):
    """
    Given a role of the agent and the beliefs of the agent build a valid strategy.
    TODO- Currently only tested on villager player because of bug in werewolves whispers.
    """

    def __init__(self, idx, role_map, agent_indices):
        self._role_probs = {}
        self._role = role_map[idx]
        self._beliefs = []
        self._alive_indices = agent_indices
        self._dead_indices = []

        # For each player index have two probabilities, the first is the probability of cooperation and the other
        # is the probability of opposition.
        self._cooperator_probs = {}

        # All lies that we have found. Our decision whether to spread out the word or not.
        self._lies_detected = []
        self._opposing_roles = get_opposing_roles(self._role)

        for agent_index in agent_indices:
            self._beliefs[agent_index] = AgentBelief(agent_index)
            self._cooperator_probs[idx] = [0.0, 0.0]

        for agent_idx, role in role_map.items():
            curr_probs = {GameRoles.VILLAGER: 0.0, GameRoles.WEREWOLF: 0.0, GameRoles.BODYGUARD: 0,
                          GameRoles.MEDIUM: 0.0, GameRoles.POSSESSED: 0.0, GameRoles.SEER: 0.0, GameRoles[role]: 1.0}
            self._role_probs[agent_idx] = curr_probs
            self._beliefs[agent_index].set_role(role)

            # Update the probability of cooperation or opposition of the agent based on the role.
            if GameRoles[role] in self._opposing_roles:
                self._cooperator_probs[agent_index][1] = 1.0
            else:
                self._cooperator_probs[agent_index][0] = 1.0

    def update_beliefs(self, diff_data):
        """
        Given the diff data received from the server update the beliefs of the agents
        based on the sentences received from them.
        :param diff_data: Pandas dataframe showing what happened during the day, what did the agents say.
        :return: None
        """
        for i in range(len(diff_data.index)):
            curr_index = diff_data.loc[i, 'agent']

            if curr_index in self._agent_beliefs.keys():
                self._agent_beliefs[diff_data.loc[i, 'agent']].update_belief(diff_data[:(i + 1)])

        # Clean all agents that died in this update.
        to_be_removed = []
        for arr_idx, agent_idx in self._alive_indices:
            if self._beliefs[agent_idx].get_status() != "ALIVE":
                self._dead_indices.append(arr_idx)

        for idx in to_be_removed:
            del self._alive_indices[idx]

        self.find_matching_admitted_roles()

        # Find the quiet agents that don't talk much, they are suspicious.

    def find_matching_admitted_roles(self):
        """
        Find if there are any agents that admitted to the same role which is not a villager (special roles).
        If two agents admit that they are werewolves they are dumbasses and probably should die.
        If there is such a case one of them is lying.
        :return:
        """
        admitted_roles = {}
        for idx in self._alive_indices:
            admitted = self._beliefs[idx].get_admitted_role()
            if admitted.role in SINGULAR_ROLES:
                # If the agent admitted to a taken role, he is a potential liar.
                if admitted.role in admitted_roles.keys():
                    potential_liar = admitted_roles[admitted.role]
                    self._lies_detected.append(Lie(potential_liar.reason, admitted.reason))
                elif admitted.role == self._role:
                    # TODO-This is the case where someone admitted to have my role. Need to expose him.
                    pass

                else:
                    admitted_roles[admitted.role] = {"idx": idx, "reason": admitted.reason}

    def get_max_at_role(self, role):
        """
        Get the agent that has the max probability of having a specific role.
        :param role:
        :return:
        """
        max_idx = 0
        max_prob = 0
        for idx, roles in self._role_probs.items():
            if roles[role] > max_prob:
                max_prob = roles[role]
                max_idx = idx

        return max_idx

    def vote(self):
        if self._role == GameRoles.VILLAGER:
            return self.get_max_at_role(GameRoles.WEREWOLF)

    def talk(self):
        if self.role == GameRoles.VILLAGER:
            # Check if there are any lies, inform everyone.
            if len(self._lies_detected) > 0:
                lie = self._lies_detected[0]

    def whisper(self):
        pass

    def attack(self):
        pass

    def divine(self):
        pass
