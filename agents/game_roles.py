from enum import Enum


class GameRoles(Enum):
    VILLAGER = 1,
    WEREWOLF = 2,
    SEER = 3,
    BODYGUARD = 4,
    POSSESSED = 5,
    MEDIUM = 6


# All the roles that only one agent can have.
SPECIAL_ROLES = [GameRoles.SEER, GameRoles.BODYGUARD, GameRoles.MEDIUM]
