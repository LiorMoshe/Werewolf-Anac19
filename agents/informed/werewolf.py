from agents.informed.informed import Informed
from agents.information_processing.agent_strategy import WolfStrategy
import numpy as np


class Werewolf(Informed):  #TODO - how to anderstend and evluate the masseges

    def __init__(self):
        self.next_attack = None
        pass

    def init_strategy(self, base_info, diff_data, game_setting):
        self._strategy = WolfStrategy([i for i in range(1, self._game_settings._player_num)
                            if i != self._base_info._agentIndex],
                            self._base_info._agentIndex,
                            self._base_info._role_map)

    def getName(self):
        return "Werewolf"

    def talk(self):
        return "COMINGOUT Agent[01] SEER"

    def whisper(self):
        if len(self._base_info._role_map) <= 1:
            pass
        if self._base_info._day == 0:
            return self._strategy._teammatestrategy.dayone()

        #my attack shoud happen once affter voting in day

        if len(self.react) > 0:
            return self.anser()
        elif len(self.conflict) > 0:
            return self.resolve_conflict()
        elif self.next_attack == None:
            get_best_agent_for_me_or_team = 1  #TODO - REQUEST ANY (IDENTIFIED Agent1 [species])” or if at risk
            reason="I dont know"
            return f"BECAUSE ({reason}) (ATTACK Agent{get_best_agent_for_me_or_team})"  #because ()() anter args
        else:
            return "OVER"
        #tree or pass or new task?
        return #f"AND (REQUEST ANY (COMINGOUT Agent{} [{}])(REQUEST ANY (COMINGOUT Agent{} [{}])"

    def vote(self):
        return "1"

    def attack(self):
        attack_chosen = np.random.choice([my_attack, team_attack,spichel_attack], p=[my_risk, team_risk,random_risk])
        return str(attack_chosen)

    def divine(self):
        pass

    def guard(self):
        pass

    def extract_state_info(self, base_info):
        pass

    def get_bff(self):
        vote_for = self.get_best_vote_opt()

        score = 1  # get_risk(vote_for)
        vote_for_bff = np.max((s, coop) for s, coop in
                              self._strategy._perspectives[vote_for].get_closest_cooperators(self._base_info._day) if
                              coop not in self._base_info._role_map)[1]
        vote_avrg_max_evel = 1  # get_avrg_obsical()
