from aiwolfpy.contentbuilder import *
from ..game_roles import GameRoles


class Lie(object):
    """
    Representation of a lie in the game. If a player is caught in a lie we want to keep it and work based
    on our role:
    A villager will always expose the lie straight up.
    A werewolf can keep it to himself and talk about it in the night phase to know who to attack.
    """

    def __init__(self, first_statement, second_statement):
        self._statements = []
        self._statements.append(first_statement)
        self._statements.append(second_statement)

    def get_subjects(self):
        subjects = []
        for statement in self._statements:
            subjects.append(statement.subject)
        return subjects

    def to_str(self):
        """
        TODO- What if one of the potential liers is a well known cooperator? Don't estimate him as a werewolf!
        If one of the subjects is trustworthy blame the others of being a werewolf or possessed.
        :return:
        """
        subjects = self.get_subjects()
        xor_werewolf = "XOR(" + estimate(subjects[0], GameRoles.WEREWOLF) + ")(" + \
                                estimate(subjects[1], GameRoles.WEREWOLF) + ")"
        return "BECAUSE (AND(" + self._statements[0] + ")(" + self._statements[1] + "))(" + \
            + xor_werewolf + ")"
