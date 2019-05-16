from agents.game_roles import GameRoles

class PlayerPerspective():
    def __init__(self, agent_indices):
        self.agent_2_threat={id: {} for id in agent_indices} # dictionary of agents -> dictionary of agents vote count
        self.prev_votes_map = {id: {} for id in agent_indices}


    #based on msg - count
    def update_potential_vote_count(self, subject, target, role = None):
        '''
        Currently counts #times subject turned against target
        :param subject:
        :param target:
        :param role:
        :return:
        '''
        if role == GameRoles.WEREWOLF or role is None:# and (subject not in self.agent_2_threat[target])
            self.agent_2_threat[target][subject] = self.agent_2_threat[target].setdefault(subject,0) + 1


    #TODO: update under heat logic setter

    def update_threat_func_val(self, non_coop, agent_id):
        weights = [0.6, 0.2, 0.2]
        prev_votes_val = sum([v/len(self.prev_votes_map) for k,v in self.prev_votes_map[agent_id]])
        curr_votes_val = sum([v/len(self.agent_2_threat) for k,v in self.agent_2_threat[agent_id]])
        return weights[0]*non_coop + weights[1]*prev_votes_val + weights[2]*curr_votes_val

    def new_day(self):
        for agent_id,dic in self.agent_2_threat.items():
            self.prev_votes_map = {**self.agent_2_threat, **self.prev_votes_map}
            self.agent_2_threat[agent_id]= self.agent_2_threat.fromkeys(self.agent_2_threat, 0)

    # def msg_event(self, msg):
