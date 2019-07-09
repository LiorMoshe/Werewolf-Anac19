from agents.information_processing.agent_perspective import *
from agents.information_processing.message_parsing import *
from agents.information_processing.sentences_container import SentencesContainer
from agents.game_roles import GameRoles
from agents.information_processing.dissection.sentence_dissector import SentenceDissector
from agents.strategies.agent_strategy import TownsFolkStrategy, MessageType
from agents.tasks.seer_task import SeerTask
import numpy as np 
import pandas as pd

class SeerStrategy(TownsFolkStrategy):
    weights_dict = {
        'W_liar': 0.3,
        'W_admitted_wolf': 0.1,
        'W_likely_wolf': 0.1,
        'W_known_wolf_coop': 0.4,
        'W_known_humans_coop': -0.2,
        'W_likely_wolf_coop': 0.25,
        'W_likely_humans_coop': -0.1,
        'W_known_wolvss_noncoop': -0.2,
        'W_likely_wolves_noncoop': -0.1,
        'W_known_humans_noncoop': 0.2,
        'W_likely_humans_noncoop': 0.2,
        'W_num_of_total_votes': 0.1,
        'W_num_of_current_votes': 0.2,
        'W_was_requested': 0.2
    }

    # convert the dict to weight vector
    weights = np.asarray(list(weights_dict.values()))

    HUMAN = "HUMAN"
    WEREWOLF = "WEREWOLF"

    DECAY_FACTOR = 0.9
    PROB_OF_REVEAL = 0.7
    PROB_OF_REVEAL_ALL = 0.4
    PROB_OF_COMINGOUT = 0.6

    def __init__(self, agent_indices, my_index, role_map, statusMap, player_perspective):
        super().__init__(agent_indices, my_index, role_map, player_perspective)

        self.my_index = my_index
        self._divined_agents = {}
        self.day_num = 0

        self.is_first_day = True

        # agents that other agents requested them to be divined
        self.requested_divine = {}

        # create prospect map {agent Idx -> suspicious score}
        self._divine_prospects = {}
        my_index_str = str(my_index)
        for agent in statusMap.keys():
            if (agent != my_index_str):
                self._divine_prospects[agent] = 0
        
        self._player_perspective = player_perspective
        
        self._seer_tasks = []

        # how many agents cameout as seers at current day
        self.count_seer_comingout = 0

        # how many times agents named me as a werewolf
        self.werewolf_accused_counter = 0

    def update_divine_result(self, agent, species):
        # no longer a prospect
        try:
            del self._divine_prospects[str(agent)]
            print("PROSPECTS")
            print(self._divine_prospects)
        except Exception as e:
            print("ERRRORRRRR {}".format(e))

        self._divined_agents[str(agent)] = species
        self.print_divined_agents()

    def print_divined_agents(self):
        print("DIVINED LIST:")
        print(self._divined_agents)

    def get_next_divine(self):
        try:
            print("****** GOT DIVINE REQUEST *******")
            # if first day no prior knowledge -> random divine
            if self.is_first_day:
                ls = list(self._divine_prospects.keys())
                idx = np.random.randint(0, len(ls))
                self.is_first_day = False
                self.day_num += 1

                return ls[idx]

            dead_agents = []

            # use prior knowledge to update prospect list
            for agent in self._divine_prospects:
                score = 0
                agent_idx = int(agent)
                feature_vec = np.zeros(SeerStrategy.weights.shape)
                
                if (self._perspectives[agent_idx]._status == AgentStatus.DEAD_WEREWOLVES):
                    # If was attacked then definitly NOT a werewolf (if possessed then seer can't know anyhow)
                    if (agent not in self._divined_agents):
                        self._divined_agents[agent] =  SeerStrategy.HUMAN
                    
                    dead_agents.append(agent)
                    continue
                
                if (self._perspectives[agent_idx]._status == AgentStatus.DEAD_TOWNSFOLK):
                    dead_agents.append(agent)
                    continue

                # look on features and use weights to calculate score
                perspective = self._perspectives[agent_idx]
                feature_vec[0] = perspective._liar_score 
                
                if (perspective._admitted_role == GameRoles.WEREWOLF):
                    feature_vec[1] = 1

                if (perspective._likely_role == GameRoles.WEREWOLF):
                    feature_vec[2] = 1

                # iterate over cooperators and non_cooperators
                self.get_cooperators_non_cooperators_features(perspective, feature_vec)
                
                feature_vec[11] = self._player_perspective.agent_2_total_votes[agent_idx]
                feature_vec[12] = self._player_perspective.agent_2_total_votes_curr_turn[agent_idx]
                if (agent_idx in self.requested_divine):
                    feature_vec[13] = 1
                print("agent {}  {}".format(agent_idx, feature_vec))
                # calculate the suspicious score
                score = feature_vec.dot(SeerStrategy.weights)

                former_score = self._divine_prospects[agent]
                decay_factor = SeerStrategy.DECAY_FACTOR ** self.day_num 
                self._divine_prospects[agent] = (decay_factor * former_score) + score

            # clean prospects that are dead (not in previous loop since it causes side effect to change object during iteration)
            for dead_agent in dead_agents:
                try:
                    del self._divine_prospects[dead_agent]
                except:
                    pass

            self.requested_divine.clear()
            self.werewolf_accused_counter = 0
            self.count_seer_comingout = 0
            self._player_perspective.under_heat_value[self.my_index] *= SeerStrategy.DECAY_FACTOR
            
            self.day_num += 1
            # decidey
            try:
                agent_to_divine = max(self._divine_prospects.keys(), key=(lambda key: self._divine_prospects[key]))
            except:
                # if somehow the prospect list is empty
                return str(1)
            print("****** END DIVINE REQUEST *******")
            return str(agent_to_divine)
        except:
            return "1"

    def get_cooperators_non_cooperators_features(self, perspective, feature_vec):
        try:
            known_werewolves_in_cooperators = 0
            known_humans_in_cooperators = 0
            likely_werewolves_in_cooperators = 0
            likely_humans_in_cooperators = 0
            for coop in perspective._cooperators:
                # if i'm a cooperator
                if (coop == self.my_index):
                    known_humans_in_cooperators += 1
                    continue
                # check if a known werewolf in cooperators
                if (str(coop) in self._divined_agents):
                    if (self._divined_agents[str(coop)] == SeerStrategy.WEREWOLF):
                        known_werewolves_in_cooperators += 1
                    elif (self._divined_agents[str(coop)] == SeerStrategy.HUMAN):
                        known_humans_in_cooperators += 1
                else: # look at likely role
                    if (self._perspectives[coop]._likely_role == GameRoles.WEREWOLF):
                        likely_werewolves_in_cooperators += 1
                    else:
                        likely_humans_in_cooperators += 1
                
            known_werewolves_in_non_cooperators = 0
            known_humans_in_non_cooperators = 0
            likely_werewolves_in_non_cooperators = 0
            likely_humans_in_non_cooperators = 0
            for noncoop in perspective._noncooperators:
                # if i'm a noncooperator
                if (noncoop == self.my_index):
                    known_humans_in_non_cooperators += 1
                    continue
                # check if a known werewolf in non cooperators
                if (str(noncoop) in self._divined_agents):
                    if (self._divined_agents[str(noncoop)] == SeerStrategy.WEREWOLF):
                        known_werewolves_in_non_cooperators += 1
                    elif (self._divined_agents[str(noncoop)] == SeerStrategy.HUMAN):
                        known_humans_in_non_cooperators += 1
                else: # look at likely role
                    if (self._perspectives[noncoop]._likely_role == GameRoles.WEREWOLF):
                        likely_werewolves_in_non_cooperators += 1
                    else:
                        likely_humans_in_non_cooperators += 1

            feature_vec[3] = known_werewolves_in_cooperators
            feature_vec[4] = known_humans_in_cooperators
            feature_vec[5] = likely_werewolves_in_cooperators
            feature_vec[6] = likely_humans_in_cooperators
            feature_vec[7] = known_werewolves_in_non_cooperators
            feature_vec[8] = likely_werewolves_in_non_cooperators
            feature_vec[9] = known_humans_in_non_cooperators
            feature_vec[10] = likely_humans_in_non_cooperators
        except:
            feature_vec[3] = 0
            feature_vec[4] = 0
            feature_vec[5] = 0
            feature_vec[6] = 0
            feature_vec[7] = 0
            feature_vec[8] = 0
            feature_vec[9] = 0
            feature_vec[10] = 0

    def generate_talk(self):
        try:
            importance = 1000
            heat_comingout = 12

            print("UNDER HEAT {}".format(self._player_perspective.under_heat_value[self.my_index]))
            if (self._player_perspective.under_heat_value[self.my_index] > heat_comingout):
                # comingout as seer
                task = SeerTask(importance, self.day_num, [self.my_index], self.my_index, comingout=True)
                self._seer_tasks.append(task)

                heat = self._player_perspective.under_heat_value[self.my_index] - 3

                try:
                    new_heat = max(0, heat)
                except:
                    new_heat = heat
                self._player_perspective.under_heat_value[self.my_index] = new_heat

                return
                #return "COMINGOUT Agent[{0:02d}] SEER".format(self.my_index)

            # consider to out myself if someone is comingout as seer
            coin = np.random.rand()
            if (coin > SeerStrategy.PROB_OF_COMINGOUT and self.count_seer_comingout > 0):
                task = SeerTask(importance, self.day_num, [self.my_index], self.my_index, comingout=True)
                self._seer_tasks.append(task)
                return

            coin = np.random.rand()        
            is_werewolf_detected = SeerStrategy.WEREWOLF in self._divined_agents.values()
            # whether to reveal info
            if (coin < SeerStrategy.PROB_OF_REVEAL and is_werewolf_detected):
                # check to see if there is a known werewolf
                werewolves = [(key, value, self._player_perspective.under_heat_value[int(key)]) for key, value in self._divined_agents.items() if value == SeerStrategy.WEREWOLF]
                # get the prospect with the most heat

                try:
                    prospect, val, heat = max(werewolves, key=lambda item: item[2])
                except:
                    prospect, val, heat = werewolves[0]

                prospect = int(prospect)

                coin = np.random.rand()

                # convince a known human to believe that prospect is a werewolf
                if (coin > SeerStrategy.PROB_OF_REVEAL_ALL):
                    if (SeerStrategy.HUMAN in self._divined_agents.values()):
                        humans = [key for key, value in self._divined_agents.items() if value == SeerStrategy.HUMAN]
                        
                        # check if one of the humans is in prospect's non cooperators
                        target = self.get_target(prospect, humans, self._perspectives[prospect]._noncooperators)

                        if (target is not None):
                            print("chose non cooperator")
                            task = SeerTask(importance, self.day_num, [target, prospect], self.my_index, target=target, prospect=prospect)
                            self._seer_tasks.append(task)
                            return
                            #return "REQUEST Agent[{0:02d}] ".format(target) + "(ESTIMATE Agent[{0:02d}] WEREWOLF)".format(prospect)

                        # check if one of the humans is in prospect's cooperators
                        target = self.get_target(prospect, humans, self._perspectives[prospect]._cooperators)

                        if (target is not None):
                            print("chose cooperator")
                            task = SeerTask(importance, self.day_num, [target, prospect], self.my_index, target=target, prospect=prospect)
                            self._seer_tasks.append(task)
                            return
                            #return "REQUEST Agent[{0:02d}] ".format(target) + "(ESTIMATE Agent[{0:02d}] WEREWOLF)".format(prospect)

                        # else - send to random human
                        target = str(np.random.choice(humans))
                        print("chose random")
                        task = SeerTask(importance, self.day_num, [target, prospect], self.my_index, target=target, prospect=prospect)
                        self._seer_tasks.append(task)
                        return
                        #return "REQUEST Agent[{0:02d}] ".format(target) + "(ESTIMATE Agent[{0:02d}] WEREWOLF)".format(prospect)
                    else:
                        # no humans
                        print("chose everybody")
                        target = "ANY"
                        task = SeerTask(importance, self.day_num, [target, prospect], self.my_index, target=target, prospect=prospect)
                        self._seer_tasks.append(task)
                        return
                        #return "REQUEST ANY (ESTIMATE Agent[{0:02d}] WEREWOLF)".format(prospect)
                else:
                    # tell everybody about prospect
                    print("chose everybody")
                    target = "ANY"
                    task = SeerTask(importance, self.day_num, [target, prospect], self.my_index, target=target, prospect=prospect)
                    self._seer_tasks.append(task)
                    return
                    #return "REQUEST ANY (ESTIMATE Agent[{0:02d}] WEREWOLF)".format(prospect)
        except:
            task = SeerTask(importance, self.day_num, [self.my_index], self.my_index, comingout=True)
            self._seer_tasks.append(task)
            return 

    def get_target(self, agent, known_humans, agent_dict):
        ls = []
        for human in known_humans:
            if (int(human) in agent_dict):
                ls.append(int(human))
        
        return int(np.random.choice(ls))

    def get_likely_to_be_voted(self, agents_list):
        try:
            highest_score = 0
            vote_id = -1
            for agent in agents_list:
                # calculate chance
                score = self._player_perspective.agent_2_total_votes[int(agent)]
                heat = self._player_perspective.under_heat_value[int(agent)]
                if (heat is None):
                    heat = 0
                
                score += heat
                # update vote score for each of the wolves
                self._perspectives[int(agent)]._vote_score = score 
                if (highest_score <= score):
                    highest_score = score
                    vote_id = agent

            print("****** vote to {} *******".format(vote_id))
            return str(vote_id)
        except:
            return "1"

    def vote(self):
        try:
            print("****** GOT VOTE REQUEST *******")
            real_wolves = []
            # check for actual wolves
            for agent in self._divined_agents:
                if (self._divined_agents[agent] == SeerStrategy.WEREWOLF):
                    real_wolves.append(agent)
            
            # if we divined some wolves, pick the one with the highest score to be out
            if (len(real_wolves) > 0):
                print("*****real wolves.********")
                v = self.get_likely_to_be_voted(real_wolves)
                if (v is not None):
                    return v
            else:
                # no divined wolves
                print("*****no divined wolves.********")
                from collections import Counter
                counter = Counter(self._divine_prospects)
                top_3_suspects = counter.most_common(3)
                print("SUSPECTS {}".format(top_3_suspects))
                top_3_suspects = [agent for agent, score in top_3_suspects]

                v = self.get_likely_to_be_voted(top_3_suspects)
                if (v is not None):
                    return v 

            return super().vote()
        except:
            return "1"

    def digest_sentences(self, diff_data):
        try:
            for i, row in diff_data.iterrows():
                # look for requests
                if ("REQUEST" in row["text"] and "DIVINATION" in row["text"]):
                    agent_to_divine = row["text"].split("DIVINATION")[1]
                    start = "Agent["
                    end = "]"
                    agent_to_divine = int(agent_to_divine[agent_to_divine.find(start) + len(start):agent_to_divine.rfind(end)])

                    print("request for divine agent {}".format(agent_to_divine))

                    self.requested_divine[agent_to_divine] = None

                # look for liars / agents that pretend to be me
                if (len(row["text"].split()) == 3 and "COMINGOUT" in row["text"] and "SEER" in row["text"]):
                    agent = int(row['agent'])
                    tmp_str = row["text"]
                    start = "COMINGOUT Agent["
                    end = "]"
                    pretender = int(tmp_str[tmp_str.find(start) + len(start):tmp_str.rfind(end)])

                    if (agent == pretender and agent != self.my_index):
                        print("PRETENDER {} {}".format(agent, pretender))
                        self._perspectives[agent].lie_detected()
                        self.count_seer_comingout += 1

                # check if i'm under attack - agents are trying to vote me out
                substr = "VOTE Agent[{0:02d}]".format(self.my_index)
                if ("REQUEST" in row["text"] and substr in row["text"]):
                    print("WANTED TO VOTE ME")
                    self._player_perspective.under_heat_value[self.my_index] += 1
                
                # if people view me as a werewolf
                substr = "Agent[{0:02d}] WEREWOLF"
                if (substr in row["text"]):
                    print("CALLED ME WOLF")
                    self._player_perspective.under_heat_value[self.my_index] += 1
                    self.werewolf_accused_counter += 1
        except:
            return

    #override
    def generate_tasks(self, game_graph, day):
        tasks = super().generate_tasks(game_graph, day)

        # add my tasks
        tasks.extend(self._seer_tasks)

        self._seer_tasks = []
        return tasks

    #override
    def update(self, diff_data, request):
        super().update(diff_data, request)

        if (request == "TALK"):
            # preprare tasks
            self.generate_talk()

'''
DIVINE STRATEGY
for each agent in prospects:
    look at perspective :
        agent status:
            if dead then remove from prospects.

            if killed by werewolfs then:
                1. definitly human.
        
        liar score 0.3
        admitted role 0.1
        likely role 0.1

        check if a known werewolf in cooperators 0.4 * (num of wolves)
        how many known humans in coopopertors: k * -0.2 
        how many known wolfs in enemies: m * -0.2

        check if a likely werewolf in cooperators 0.25 * (num of wolves)
        how many likely humans in coopopertors: k * -0.1 
        how many likely wolfs in enemies: m * -0.1

        check number of votes

        how many agents voted for this agent this turn

        each day:
            decay_factor * prev score + current score 


TALK STRATEGY

COMINGOUT / ESTIMATE - only if prior knowledge exists about werewolves:
    1. either speak out loud to everyone:
        REQUEST ANY (ESTIMATE Agent1 [role])
    2. request known humans to change their mind about certain players :
        REQUEST Agent1 (ESTIMATE Agent2 [role])
COMINGOUT as seer only if my risk of being voted out is high

check for inquries or requests of divine, if so add a special feature (1 if an agent
was requested to be divined by another agent)

randomly choose skip

VOTE STRATEGY

check if a known werewolf in divined list, if so vote to the one with the highest
chances to be executed.

else, pick top 3 suspects in prospects and vote to the one with the highest chances
to be executed.

highest chance = known previous votes + risk 



1. consider comingout as seer if someone else did
2. fix under heat level.. maybe use an internal variable

'''