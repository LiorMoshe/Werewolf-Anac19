from agents.game_roles import GameRoles

class PlayerPerspective(object):

    def __init__(self, agent_indices):
        # Represent current agent's chance to be voted out of the game
        #TODO: Maybe we shouldn't count actuall votes? in order to detect actual wolf intent
        self.agent_2_agents_votes = {agent_idx: {} for agent_idx in agent_indices} # dictionary of agents -> dictionary of agents vote count
        self.prev_votes_map = {agent_idx: {} for agent_idx in agent_indices}
        self.under_heat_value = {agent_idx:0 for agent_idx in agent_indices}
        self.talk_num_2_target = {}
        self.agent_2_total_votes = {}

    #based on msg - count
    def update_potential_vote_data(self, subject, target, talk_number):
        '''
        Currently counts #times subject turned against target
        :param subject:
        :param target:
        '''
        self.talk_num_2_target[talk_number] = target
        self.agent_2_agents_votes[target][subject] = self.agent_2_agents_votes[target].setdefault(subject, 0) + 1

    def update_threat_func_val(self, non_coop, agent_id):
        weights = [0.6, 0.2, 0.2]
        prev_votes_val = sum([v/len(self.prev_votes_map) for k,v in self.prev_votes_map[agent_id]])
        curr_votes_val = sum([v / len(self.agent_2_agents_votes) for k, v in self.agent_2_agents_votes[agent_id]])
        return weights[0]*non_coop + weights[1]*prev_votes_val + weights[2]*curr_votes_val

    # TODO: Listen to new-day
    def new_day(self):
        '''
        Add votes to prev_votes_map and reset current turns potential votes
        '''
        for agent_id,dic in self.agent_2_agents_votes.items():
            self.prev_votes_map = {**self.agent_2_agents_votes, **self.prev_votes_map}
            self.agent_2_agents_votes[agent_id]= self.agent_2_agents_votes.fromkeys(self.agent_2_agents_votes, 0)

    def end_of_day(self):
        '''
        at the end of the day, sums all votes per agent
        :return:
        '''
        for agent_id, dic in self.agent_2_agents_votes.items():
            self.agent_2_total_votes[agent_id] = sum(dic.values())

    # Knowledge = namedtuple('Knowledge', 'subject target role type reason day described_day')#Estimate
    # Vote = namedtuple('Vote', 'subject target type reason day described_day')
    # Opinion = namedtuple('Opinion', 'subject talk_number type referencedSentence day described_day')#Agree

    # TODO: Decide if when to empty certain day's messages - talk_num_2_target - in new_day func
    def msg_event(self, msg, talk_number):
        fields = msg._fields
        subject = msg['subject']
        target = None
        if 'target' in fields:
            target = msg['target']
        elif 'talk_number' in fields:
            target = self.talk_num_2_target[msg['talk_number']]
        if target is None:
            return
        role = msg['role'] if 'role' in fields else None
        if role is None or role == GameRoles.WEREWOLF:
            self.under_hit_value[target] = self.update_potential_vote_data(subject, target, role)
