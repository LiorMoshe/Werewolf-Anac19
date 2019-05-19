from agents.uninformed.villager import Villager
from agents.information_processing.agent_strategy import TownsFolkStrategy

class Bodyguard(Villager):

    def __init__(self):
        pass

    def init_strategy(self, base_info, diff_data, game_setting):
        self._strategy = TownsFolkStrategy([i for i in range(1, self._game_settings._player_num)
                            if i != self._base_info._agentIndex],
                            self._base_info._agentIndex,
                            self._base_info._role_map)

    def getName(self):
        return "Bodyguard"

    def talk(self):
        #TODO: IMPLEMENT
        return "COMINGOUT Agent[01] WEREWOLF"

    def whisper(self):
        pass

    def vote(self):
        #TODO: remove if no additional logic
        '''
        Should vote with the same logic as villager
        :return:
        '''
        return self.vote()

    def attack(self):
        pass

    def divine(self):
        pass

    def guard(self):
        pass


    def non_tested_guard(self):
        agent_id = None
        guard_score = 0
        guard_risk = 0
        #TODO: maybe add epsilon in case there is no one with 0-vote score such that anyone with vote weight below epsilon could be considered
        #TODO:IMPLEMENT THAT IF IM AT RISK I SHOULD DEFENED MYSELF
        #TODO: IF NOBODY DIED IN THE ATTACK BODYGUARD MYSELF
        if self._strategy is None:
            return self.getName()
        for id,agent_persp in self._strategy._perspectives.items():
            if agent_persp.vote_score <= guard_score and (agent_id is None or agent_persp.under_risk_level>guard_risk):
                guard_score = agent_persp.vote_score
                guard_risk = agent_persp.under_risk_level
                agent_id = id
        if agent_id is None:
            return self.getName()


    def extract_state_info(self, base_info):
        pass

