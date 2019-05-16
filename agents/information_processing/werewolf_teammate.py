from enum import Enum
import random

class AgentStatus(Enum):
    ALIVE = 1
    DEAD_TOWNSFOLK = 2,
    DEAD_WEREWOLVES = 3


class TeamStrategy:
    def __init__(self, agent_idx, my_idx, sentences_container, role=None):
        """
        :param agent_idx: Index of this agent.
        :param my_idx: Index of our agent.
        """
        self._index = agent_idx
        self.my_agent = my_idx
        self._cooperators = {}
        self._noncooperators = {}
        self._admitted_role = None
        self._assind_roles = {}
        self._status = AgentStatus.ALIVE
        # Represent current agent's change to be voted out of the game
        #TODO: implement setter + logic
        self.under_risk_level = 0
        # Messages ordered by day that are directed to me (think these are only inquire and request messages).
        self.messages_to_me = {}
        self._sentences_container = sentences_container

        self.team = []
        self.conflict = []
        self.react = []
        self.next_attack = None

    def dayone(self):
        if self._base_info._wisper[str(self.my_agent)]==1:
            humans = random.choice(self._noncooperators,2,replace=False)
            #"INQUIRE ANY (DAY 1(AGREE ANY))"
            return f"AND (INQUIRE Agent{self.team[0]} (DAY 1(AGREE Agent{humans[0]}))(INQUIRE Agent{self.team[1]} (DAY 1(AGREE Agent{humans[1]})))"
        elif len(self.conflict) > 0:
            return self.resolve_conflict()
        elif len(self.react) > 0:
            return self.anser()
        elif not (self._assind_roles):
            return "INQUIRE ANY (ESTIMATE ANY ANY)"  # ask players to assign rolls
        else:
            return "OVER"

    def resolve_conflict(self):
        prob = self.conflict.pop()
        choosen = self.check_option(prob[0],prob[1])
        return f"BECAUSE (AND({prob[choosen]})({prob[1-choosen]})) (AND({prob[choosen]})(NOT({prob[1-choosen]})))"

    def anser(self):
        anser = "AND"
        for event in self.react:
            anser += f"({event})"
        return anser

    def check_option(self,option1,option2):
        return 0

    def get_best_attak_for_team(self):
        for w in self.team:
            w.under_risk_level
        return 1  #TODO

