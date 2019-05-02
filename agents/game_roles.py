from enum import Enum


class GameRoles(Enum):
    VILLAGER = 1,
    WEREWOLF = 2,
    SEER = 3,
    BODYGUARD = 4,
    POSSESSED = 5,
    MEDIUM = 6


TOWNSFOLK = [GameRoles.VILLAGER, GameRoles.SEER, GameRoles.BODYGUARD, GameRoles.MEDIUM]
WEREWOLVES = [GameRoles.WEREWOLF, GameRoles.POSSESSED]

# These are roles that only a single player can have.
SINGULAR_ROLES = [GameRoles.BODYGUARD, GameRoles.SEER, GameRoles.MEDIUM]


def get_opposing_roles(role):
    """
    Get the opposing team based on a given role.
    :param role:
    :return:
    """
    return TOWNSFOLK if role in WEREWOLVES else WEREWOLVES
