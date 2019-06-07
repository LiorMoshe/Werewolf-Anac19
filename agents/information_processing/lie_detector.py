from agents.game_roles import *
from agents.tasks.admitted_role_task import AdmittedRoleTask

# Importance of the task of two lying agents detected.
ADMITTED_ROLE_IMPORTANCE = 1.0

# Importance of the task when one or more agents admitted to have my role.
MY_ADMITTED_ROLE_IMPORTANCE = 2.0


# class Lie(object):
#
#     def __init__(self, potential_liars, reasons):
#         self._potential_liars = potential_liars
#
#     def get_lying_score(self):
#         return 1 / len(self._potential_liars)


class LieDetector(object):
    """
    Given a set of agent's perspectives run a series of tests to detect matches that show that at least
    one of the agents is lying. This will help us know the trustworthiness of other agents in the game.
    """

    def __init__(self, my_index, agent_indices, role):
        self.index = my_index
        self.role = role
        self._agent_lies = {}
        for idx in agent_indices:
            self._agent_lies[idx] = []

    def find_matching_admitted_roles(self, perspectives, day):
        """
        Go over our agents and see which ones are caught lying, each caught liar
        will be given a lying score and it will create a task that may be handled by us sometimes
        in the future.
        :param perspectives: All perspectives of agents that are still in the game.
        :param day Current day in the game.
        :return:
        """

        # Initialize admitted roles in the game with my role.
        roles = {self.role: [{"index": self.index}]}
        for perspective in perspectives.values():
            admitted_role = perspective.get_admitted_role()
            if admitted_role is not None:
                str_admitted_role = str(admitted_role["role"])
                if str_admitted_role not in roles.keys():
                    roles[str_admitted_role] = [{"index": perspective.get_index(), "ref": admitted_role["reason"]}]
                else:
                    roles[str_admitted_role].append({"index": perspective.get_index(), "ref": admitted_role["reason"]})

        # Go over all admitted roles and see if you can generate any tasks.
        tasks = []
        for role, admitted_players in roles.items():
            admitted_refs = []
            agent_indices = []

            # If there is more than one player and the role is a special role we caught a liar.
            if len(admitted_players) > 1 and role in SPECIAL_ROLES:
                for player in admitted_players:
                    player_index = player["index"]

                    if player_index != self.index:
                        admitted_refs.append(player["ref"])

                    agent_indices.append(player_index)

                importance = MY_ADMITTED_ROLE_IMPORTANCE if self.index in agent_indices else ADMITTED_ROLE_IMPORTANCE
                tasks.append(AdmittedRoleTask(importance, day, agent_indices, role, admitted_refs, self.index))

                # Update the perspectives of players, let them know we found a lie.
                for idx in agent_indices:
                    if idx != self.index:
                        perspectives[idx].lie_detected()

        return tasks

if __name__ == "__main__":
    # Create two perspectives and check if the matching works
    from agents.logger import Logger
    from agents.game_roles import GameRoles
    from agents.information_processing.sentences_container import SentencesContainer
    from agents.information_processing.agent_perspective import AgentPerspective
    Logger("log.txt")

    first_persp = AgentPerspective(1, 10)
    first_persp._admitted_role = {"role": GameRoles.SEER, "reason": "Lior is the king."}

    second_persp = AgentPerspective(2, 10)
    second_persp._admitted_role = {"role": GameRoles.SEER, "reason": "Joseph is the king"}

    perspectives = {1: first_persp, 2: second_persp}

    lie_detector = LieDetector(10, [1,2], str(GameRoles.SEER))
    tasks = lie_detector.find_matching_admitted_roles(perspectives, 1)

    print(tasks[0].handle_task())
    print("DONE")