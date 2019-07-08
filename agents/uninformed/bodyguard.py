from agents.uninformed.villager import Villager
from agents.information_processing.agent_perspective import AgentStatus
import aiwolfpy.contentbuilder as cb
from agents.game_roles import GameRoles
import numpy as np
from agents.strategies.agent_strategy import TownsFolkStrategy

DEFAULT_MODE = 0
RISK_MODE = 1
POST_RISK_MODE = 2

class Bodyguard(Villager):
    def __init__(self):
        self.last_guarded = None
        self.mode = DEFAULT_MODE
        self.last_attacked = None
        self.self_guard_score = None
        #human,votelist tuple
        self.succ_guarded = []

    def init_strategy(self, base_info, diff_data, game_setting):
        self._strategy = TownsFolkStrategy([i for i in range(1, self._game_settings._player_num)
                            if i != self._base_info._agentIndex],
                            self._base_info._agentIndex,
                            self._base_info._role_map, self._player_perspective)

    def vote(self):
        return self._strategy.vote()

    def getName(self):
        return "Bodyguard"

    def talk(self):
        try:
            msg = ""
            if self.last_guarded is not None:
                self.last_guarded = int(self.last_guarded)
            self._player_perspective.update_total_vote_count()
            if self._player_perspective.agent_2_total_votes[self.player_id] >= self._game_settings._player_num/2 and self.mode == DEFAULT_MODE:
                self.mode = RISK_MODE
                self.self_guard_score = np.inf
                print("BODYGUARDMSG:Risk Mode")
            if self.mode == RISK_MODE:
                msg1 = self.get_agent_string(self.player_id) + " " + "AND (" + cb.comingout(self.player_id, "BODYGUARD") + ")"
                for agent, voting_agents in self.succ_guarded:
                    agent = int(agent)
                    msg1 += "AND (BECAUSE (AND (" + cb.guarded(agent) +")(NOT (ANY ATTACKED " + self.get_agent_string(agent) + "))) (" + cb.comingout(agent, "VILLAGER") + "))"
                self.self_guard_score = self.self_guard_score - 3 if self.self_guard_score is not None else 3
                self.mode = POST_RISK_MODE


            # elif len(self.succ_guarded) > 0 and self.last_attacked == None:
            #     print("IN TALK GUARD: ")
            #     print(self.succ_guarded[-1], self.last_guarded)
            #     msg = self.get_agent_string(self.player_id) + " BECAUSE ( AND "
            #     for (agent,voters) in self.succ_guarded:
            #         msg += "(" + self.get_agent_string(agent) + " VOTED " + "Agent" + str(self.last_guarded) + ")"
            #     msg += ") (AND ("+cb.comingout(self.last_guarded, "VILLAGER")+")"
            #     msg += "(OR "
            #     for (agent, voters) in self.succ_guarded:
            #         msg += "("+cb.comingout(int(agent), "WEREWOLF")+")"
            #     msg += "))"
            #TODO:
            # pick most aggressive voter or one that was in most of other votes or union
        except:
            return Villager.talk(self)
                # set special mode in order to prevent coming out multiple times ?
        return Villager.talk(self) if msg == "" else msg
        #TODO: IF GUARDED DID NOT DIE SAY HE IS HUMAN BECAUSE THEY ATTACKED HIM and then guardmyself and raise my risk function

    def guard(self):
        return self.non_tested_guard()

    def non_tested_guard(self):
        try:
            if self._player_perspective.agent_2_total_votes[self.player_id] >= self._game_settings._player_num / 2:
                return self.player_id
            guard_score = np.inf if self.self_guard_score is None else self.self_guard_score
            print("BODYGUARDMSG:Initial Guard Score "+str(guard_score))
            my_risk_val = self._player_perspective.under_heat_value[self.player_id]
            guard_risk = my_risk_val
            print("my risk val: "+str(guard_risk))
            guarding_list = []

            for id,agent_persp in self._strategy._perspectives.items():
                # Skip dead Mr's and Mr's who have higher vote score than my guard score
                if agent_persp._status != AgentStatus.ALIVE or agent_persp._likely_role == GameRoles.WEREWOLF:
                    continue

                agent_vote_score = self.get_vote_score(id)
                risk_val = self._player_perspective.under_heat_value[id]
                print("agent {0}, risk {1}, vote score {2}".format(id, risk_val, agent_vote_score))
                guarding_list.append([id, agent_vote_score, risk_val])


            if len(guarding_list) == 0:
                self.last_guarded = self.player_id
            else:
                guarding_list = np.asarray(guarding_list)
                max_vote_score = np.max(guarding_list.T[1])
                # get max risk val
                guard_risk = np.max(guarding_list.T[2].astype(float))
                print("guarding list {0} max vs {1} risk {2}".format(str(guarding_list), max_vote_score, guard_risk))
                # Decrease voting score in guarding list for agents who are far less "votable" - so that when we reverse
                # the scoring we will prefer to guard them
                # sorted_vote_score = np.sort(guarding_list.T, axis=1)[1]
                # sorted_vote_score_common_values = [val for i,val in enumerate(sorted_vote_score[1:]) if abs(sorted_vote_score[i-1] - val) < 1]
                #
                # for idx, [id, vs, rv] in enumerate(guarding_list):
                #     if (max_vote_score - vs) % 100 >= 2:
                #         guarding_list[idx] = [id, max(0, max_vote_score - vs), rv]
                # for idx, [id, vs, rv] in enumerate(guarding_list):
                #     if (max_vote_score - vs) % 100 >= 2:
                #         guarding_list[idx] = [id, max(0, max_vote_score - vs), rv]
                print("guarding list {0} max vs {1} risk {2}".format(str(guarding_list), max_vote_score, guard_risk))
                # Weight guarding between vote score and risk value - prefer players who have both high risk value and low voting score
                # and try to prefer players with lower guarding score
                scores = np.asarray([-1*vs + rv for _, vs, rv in guarding_list])
                scores /= max(abs(scores))
                # Cast scores to probabilities via softmax
                probabilities = np.exp(scores) / sum(np.exp(scores))
                # Get agent ids as the new guarding list
                guarding_list = np.asarray(guarding_list).T[0]
                print("gl {0}, scores {1}".format(guarding_list, scores))

                if guard_risk <= my_risk_val:  # Guarding myself is a better option
                    epsilon = 0.3
                else:  # guard score is equal to mine
                    epsilon = 0.7
                agent_2_guard = np.random.choice(guarding_list, p=probabilities) if len(guarding_list) > 1 else guarding_list[0]
                self.last_guarded = np.random.choice([self.player_id, agent_2_guard], p=[1-epsilon, epsilon])
                print("BODYGUARDMSG:GUARD EPS " + str(epsilon))
                print(probabilities)

            print(self.last_guarded)
            if self.mode == POST_RISK_MODE:
                self.self_guard_score = None
                self.mode = DEFAULT_MODE
        except:
            try:
                min = np.inf
                id = 1
                for k,v in self._strategy._vote_model._vote_scores.items():
                    if v < min:
                        id = k
                        min = v
                return int(id)
            except:
                return self.player_id

        return self.last_guarded

    # def non_tested_guard(self):
    #     if self._player_perspective.agent_2_total_votes[self.player_id] >= self._game_settings._player_num / 2:
    #         return self.player_id
    #     agent_id = None
    #     guard_score = np.inf if self.self_guard_score is None else self.self_guard_score
    #     print("BODYGUARDMSG:Initial Guard Score "+str(guard_score))
    #     my_risk_val = self._player_perspective.under_heat_value[self.player_id]
    #     guard_risk = my_risk_val
    #     min_vote_score = np.inf
    #     print("my risk val: "+str(guard_risk))
    #     eq_guard_score = []
    #     for id,agent_persp in self._strategy._perspectives.items():
    #         # Skip dead Mr's and Mr's who have higher vote score than my guard score
    #         if agent_persp._status != AgentStatus.ALIVE or agent_persp._likely_role == GameRoles.WEREWOLF:
    #             continue
    #
    #         agent_vote_score = self.get_vote_score(id)
    #         risk_val = self._player_perspective.under_heat_value[id]
    #         print("agent {0}, risk {1}, vote score {2}".format(id, risk_val, agent_vote_score))
    #         if (agent_id is None or (risk_val>guard_risk and min_vote_score > agent_vote_score)):
    #             guard_score = agent_vote_score
    #             guard_risk = risk_val
    #             agent_id = id
    #             eq_guard_score = []
    #             eq_guard_score.append(agent_persp.get_index())
    #         elif risk_val >= guard_risk or agent_vote_score < guard_score:
    #             eq_guard_score.append(agent_persp.get_index())
    #         if agent_vote_score < min_vote_score:
    #             min_vote_score = agent_vote_score
    #
    #     if guard_risk <= my_risk_val: # Guarding myself is a better option
    #         epsilon = 0.3
    #     else: # guard score is equal to mine
    #         epsilon = 0.7
    #     print("BODYGUARDMSG:GUARD EPS "+str(epsilon))
    #     print(eq_guard_score)
    #     self.last_guarded = np.random.choice([self.player_id, self.get_agent_id_2_guard(eq_guard_score)], p=[1-epsilon, epsilon]) if len(eq_guard_score) > 0 else self.player_id
    #     print(self.last_guarded)
    #     if self.mode == POST_RISK_MODE:
    #         self.self_guard_score = None
    #         self.mode = DEFAULT_MODE
    #     return self.last_guarded

    def get_agent_id_2_guard(self, agent_ids):
        if len(agent_ids) == 1:
            return agent_ids[0]
        return np.random.choice(agent_ids, p=np.ones(len(agent_ids))/len(agent_ids))


    def extract_state_info(self, base_info, diff_data, request):
        # agent outvoted -> list of agents who voted against him
        voted_agents = {}
        if request == "DAILY_INITIALIZE":
            self.last_attacked = None
            for line_num, txt in enumerate(diff_data["type"]):
                print(line_num,txt)
                # Update attacked agent
                if txt == "dead":
                    self.last_attacked = diff_data.loc[line_num,"agent"]
                elif txt == "vote":
                    try:
                        voted_agent = int(diff_data.loc[line_num,"text"].split("[")[1][:-1])
                        voted_agents.setdefault(voted_agent, []).append(diff_data.loc[line_num,"agent"])
                    except ValueError:
                        pass

            voted_agents[self.last_guarded] = []
            if self.last_attacked is not None:
                print("BODYGUARDMSG: LAST ATTACKED "+str(self.last_attacked)+" voters "+str(voted_agents))
            else:
                print("BODYGUARDMSG: LAST ATTACKED IS NONE")
            print("lst attacked {0}, last guarded {1} voters {2}".format(self.last_attacked, self.last_guarded, voted_agents))
            if self.last_attacked is None and self.last_guarded is not None:
                print("BODYGUARDMSG: SUCCESS IN GUARD!")
                self.succ_guarded.append((self.last_guarded,voted_agents[self.last_guarded]))
                #TODO: do something with voters(against guarded) score

        # TODO:if nobody died - set agent as humans and increase vote score to contributors

    def get_agent_string(self, id):
        return "Agent ["+str(id)+"]"