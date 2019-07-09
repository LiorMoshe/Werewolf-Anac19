from agents.information_processing.agent_perspective import *
from agents.information_processing.message_parsing import *
from agents.information_processing.sentences_container import SentencesContainer
from agents.game_roles import GameRoles
from agents.information_processing.dissection.sentence_dissector import SentenceDissector
from agents.strategies.agent_strategy import TownsFolkStrategy, MessageType
from agents.tasks.medium_task import MediumTask
import numpy as np 
import pandas as pd

class MediumStrategy(TownsFolkStrategy):
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

        self._player_perspective = player_perspective
        
        self._medium_tasks = []

        # how many agents cameout as seers at current day
        self.count_medium_comingout = 0

        # how many times agents named me as a werewolf
        self.werewolf_accused_counter = 0

    def update_divine_result(self, agent, species):
        self._divined_agents[str(agent)] = species
        self.print_divined_agents()

    def print_divined_agents(self):
        print("DIVINED LIST:")
        print(self._divined_agents)

    def generate_talk(self):
        try:
            importance = 1000
            heat_comingout = 12

            print("UNDER HEAT {}".format(self._player_perspective.under_heat_value[self.my_index]))
            if (self._player_perspective.under_heat_value[self.my_index] > heat_comingout):
                # comingout as seer
                task = MediumTask(importance, self.day_num, [self.my_index], self.my_index, comingout=True)
                self._medium_tasks.append(task)

                heat = self._player_perspective.under_heat_value[self.my_index] - 3
                self._player_perspective.under_heat_value[self.my_index] = max(0, heat)
                return
                #return "COMINGOUT Agent[{0:02d}] SEER".format(self.my_index)

            # consider to out myself if someone is comingout as seer
            coin = np.random.rand()
            if (coin > MediumStrategy.PROB_OF_COMINGOUT and self.count_medium_comingout > 0):
                task = MediumTask(importance, self.day_num, [self.my_index], self.my_index, comingout=True)
                self._medium_tasks.append(task)
                self.count_medium_comingout -= 1
                return

            # identified
            if (len(self._divined_agents) > 0):
                coin = np.random.rand()

                if (coin < MediumStrategy.PROB_OF_REVEAL):
                    if (self.is_werewolf_in_divined()):
                        werewolves = list(filter(lambda agent: self._divined_agents[agent] == MediumStrategy.WEREWOLF, self._divined_agents.keys()))
                        print("identified task")
                        identified = np.random.choice(werewolves)
                        task = MediumTask(importance, self.day_num, [self.my_index], self.my_index, (identified, MediumStrategy.WEREWOLF))

                        self._medium_tasks.append(task)
        except:
            task = MediumTask(importance, self.day_num, [self.my_index], self.my_index, comingout=True)
            self._medium_tasks.append(task)
            return
        
    def is_werewolf_in_divined(self):
        divined_agents = self._divined_agents.values()
        if (MediumStrategy.WEREWOLF in divined_agents):
            return True
        
        return False

    def vote(self):
        try:
            print("****** GOT VOTE REQUEST *******")
            if (self.is_werewolf_in_divined()):
                werewolves = []
                for agent in self._divined_agents:
                    if (self._divined_agents[agent] == MediumStrategy.WEREWOLF):
                        werewolves.append(int(agent))

                # for each werewolf find its cooperators
                for werewolf in werewolves:
                    if (len(self._perspectives[werewolf]._cooperators) > 0):
                        cooperators = self._perspectives[werewolf]._cooperators.keys()

                        coop_with_heat = max(cooperators, key=lambda c: 
                                                            self._player_perspective.under_heat_value[c])
                        return str(coop_with_heat)
                return super().vote()
            else:
                v = super().vote()
                print("v is {}".format(v))
                return v
        except:
            return "1"

    def digest_sentences(self, diff_data):
        try:
            for i, row in diff_data.iterrows():
                # look for liars / agents that pretend to be me
                if (len(row["text"].split()) == 3 and "COMINGOUT" in row["text"] and "MEDIUM" in row["text"]):
                    agent = int(row['agent'])
                    tmp_str = row["text"]
                    start = "COMINGOUT Agent["
                    end = "]"
                    pretender = int(tmp_str[tmp_str.find(start) + len(start):tmp_str.rfind(end)])

                    if (agent == pretender and agent != self.my_index):
                        print("PRETENDER {} {}".format(agent, pretender))
                        self._perspectives[agent].lie_detected()
                        self.count_medium_comingout += 1

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
        tasks.extend(self._medium_tasks)

        self._medium_tasks = []
        return tasks

    #override
    def update(self, diff_data, request):
        super().update(diff_data, request)

        if (request == "TALK"):
            # preprare tasks
            self.generate_talk()



'''
TALK STRATEGY

    1. comingout if under heat or someone is a pretender.
    2. if wolves in divined list :
        check for their cooperators :
            estimate their werewolves
            or
        
        or identify random werewolf

VOTE STRAREGY


'''