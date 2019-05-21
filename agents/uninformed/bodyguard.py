from agents.uninformed.villager import Villager
from agents.information_processing.agent_perspective import AgentStatus
import aiwolfpy.contentbuilder as cb
from agents.game_roles import GameRoles
import numpy as np
from agents.information_processing.agent_strategy import TownsFolkStrategy

DEFAULT_MODE = 0
RISK_MODE = 1
POST_RISK_MODE = 2
SUCC_GUARD = 3
self_guard_score = None

class Bodyguard(Villager):
    def __init__(self):
        self.last_guarded = None
        self.mode = DEFAULT_MODE
        self.last_attacked = None
        #human,votelist tuple
        self.succ_guarded = []

    def init_strategy(self, base_info, diff_data, game_setting):
        self._strategy = TownsFolkStrategy([i for i in range(1, self._game_settings._player_num)
                            if i != self._base_info._agentIndex],
                            self._base_info._agentIndex,
                            self._base_info._role_map, self._player_perspective)

    def getName(self):
        return "Bodyguard"

    def talk(self):
        msg = ""
        self._player_perspective.update_total_vote_count()
        if self._player_perspective.agent_2_total_votes[self.player_id] >= self._game_settings._player_num/2 and self.mode == DEFAULT_MODE:
            self.mode = RISK_MODE

        if self.mode == RISK_MODE:
            msg1 = self.get_agent_strint(self.player_id) + " " +"AND ("+ cb.comingout(self.player_id, GameRoles.BODYGUARD)+")"
            for agent, voting_agents in self.succ_guarded:
                msg1 += "AND (BECAUSE (AND ("+cb.guarded(agent)+")(NOT (ANY ATTACKED "+self.get_agent_strint(agent)+"))) ("+cb.comingout(agent, GameRoles.VILLAGER)+"))"

            self.mode = POST_RISK_MODE

        elif len(self.succ_guarded) > 0 and self.last_attacked == None:
            msg = self.get_agent_strint(self.player_id) + " BECAUSE ( AND "
            for agent in self.succ_guarded[-1]:
                msg += "(" + self.get_agent_strint(agent) + " VOTED " + "Agent"+self.last_guarded + ")"
            msg += ") (AND ("+cb.comingout(self.last_guarded, GameRoles.VILLAGER)+")"
            msg += "(OR "
            for agent in self.succ_guarded[-1]:
                msg += "("+cb.comingout(agent, GameRoles.WEREWOLF)+")"
            msg += "))"
        #TODO:
        # pick most aggressive voter or one that was in most of other votes or union

                # set special mode in order to prevent coming out multiple times ?
        return Villager.talk(self) if msg == "" else msg
        #TODO: IF GUARDED DID NOT DIE SAY HE IS HUMAN BECAUSE THEY ATTACKED HIM and then guardmyself and raise my risk function

    # def whisper(self):
    #     pass

    # def vote(self):
    #     #TODO: remove if no additional logic
    #     '''
    #     Should vote with the same logic as villager
    #     :return:
    #     '''
    #     return "5"
    #
    # def attack(self):
    #     pass
    #
    # def divine(self):
    #     pass

    def guard(self):
        return "1"

    def non_tested_guard(self):
        if self._player_perspective.agent_2_total_votes[self.player_id] >= self._game_settings._player_num / 2:
            return self.player_id
        agent_id = None
        guard_score = np.inf if self_guard_score is None else self_guard_score
        guard_risk = 0
        eq_guard_score = []
        #TODO: IF NOBODY DIED IN THE ATTACK - ?
        if self._strategy is None:
            self.last_guarded = self.player_id
            return self.player_id
        for id,agent_persp in self._strategy._perspectives.items():
            if agent_persp._status != AgentStatus.ALIVE or agent_persp._likely_role == GameRoles.WEREWOLF:
                continue
            if agent_persp.vote_score <= guard_score:
                if (agent_id is None or agent_persp.under_risk_level>guard_risk):
                    guard_score = agent_persp.vote_score
                    guard_risk = agent_persp.under_risk_level
                    agent_id = id
                    eq_guard_score = []
                    eq_guard_score.append(id)
                elif agent_persp.under_risk_level == guard_risk:
                    eq_guard_score.append(agent_id)

        if guard_score > 0: # Guarding myself is a better option
            epsilon = 0.3
        else: # guard score is equal to mine
            epsilon = 0.5

        self.last_guarded = np.random.choice([self.player_id, self.get_agent_id_2_guard(eq_guard_score)], p=[1-epsilon, epsilon])
        return self.last_guarded

    def get_agent_id_2_guard(self, agent_ids):
        if len(agent_ids) == 1:
            return agent_ids[0]
        return np.random.choice([agent_ids], p=np.ones(len(agent_ids))/len(agent_ids))

    def extract_state_info(self, base_info, diff_data, request):
        # agent outvoted -> list of agents who voted against him
        voted_agents = {}
        voted_agent = None
        if request == "DAILY_INITIALIZE":
            self.last_attacked = None
            for line_num, txt in enumerate(diff_data["text"]):
                if txt == "dead":
                    self.last_attacked = diff_data["agent"][line_num]
                elif txt == "vote":
                    try:
                        voted_agent = int(txt.split("[")[1][:-1])
                        voted_agents.setdefault(voted_agent, []).append(diff_data["agent"][line_num])
                    except ValueError:
                        pass
            if voted_agent is not None and len(diff_data["text"]) >0 and self.last_attacked == None:
                self.succ_guarded.append((self.last_guarded,voted_agents[voted_agent]))
                #TODO: do something with voters(against guarded) score

        # TODO:if nobody died - set agent as humans and increase vote score to contributors

    def get_agent_strint(self, id):
        return "Agent ["+str(id)+"]"