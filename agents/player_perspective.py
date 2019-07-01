from agents.game_roles import GameRoles

class PlayerPerspective(object):

    def __init__(self, agent_indices):
        # Represent current agent's chance to be voted out of the game
        # dictionary of agents -> dictionary of agents count of negative speaking in current turn
        self.agent_2_agents_negative_talk = {agent_idx: {} for agent_idx in agent_indices}
        # dictionary of agents -> dictionary of agents vote count
        self.agent_2_agents_votes = {agent_idx: {} for agent_idx in agent_indices}
        # dictionary of agents -> dictionary of agents vote count from first turn until now(including)
        self.agent_2_prev_votes = {agent_idx: {} for agent_idx in agent_indices}
        # map of agent->under_heat_value - heuristic value that represents  being under vote risk
        self.under_heat_value = {agent_idx:0 for agent_idx in agent_indices}
        self.talk_num_2_target = {}
        # updates every diff_data of votes:
        # map of agent -> total votes so far (from the beginning of the game)
        self.agent_2_total_votes = {agent_idx:0 for agent_idx in agent_indices}
        # map of agent -> total votes this turn
        self.agent_2_total_votes_curr_turn = {agent_idx:0 for agent_idx in agent_indices}

    #based on msg - count
    #def update_potential_vote_data(self, subject, target, talk_number, non_coop):
    def update_potential_vote_data(self, subject, target, talk_number):
        '''
        Currently counts #times subject turned against target
        :param subject:
        :param target:
        '''
        self.talk_num_2_target[talk_number] = target
        self.agent_2_agents_negative_talk[target][subject] = self.agent_2_agents_negative_talk[target].setdefault(subject, 0) + 1
        #self.update_threat_func_val(non_coop, target)

    def update_threat_func_val(self, non_coop, agent_id):
        weights = [0.2, 0.2, 0.6]
        prev_votes_val = sum([v / len(self.agent_2_prev_votes) for k, v in self.agent_2_prev_votes[agent_id].items()])
        curr_votes_val = sum([v / len(self.agent_2_agents_negative_talk) for id, v in self.agent_2_agents_negative_talk[agent_id].items()])
        self.under_heat_value[agent_id] = weights[0]*non_coop + weights[1]*prev_votes_val + weights[2]*curr_votes_val

    def update(self, diff_data):
        up_total = False
        '''
        Add votes to prev_votes_map and reset current turns potential votes
        '''
        for line_num, txt in enumerate(diff_data["type"]):
            if txt == "vote":
                up_total = True
                try:
                    voted_agent = int(diff_data.loc[line_num,"text"].split("[")[1][:-1])
                    voting_agent = diff_data.loc[line_num,"agent"]
                    self.agent_2_prev_votes[voted_agent][voting_agent] = self.agent_2_prev_votes[voted_agent].setdefault(voting_agent, 0) + 1
                    self.agent_2_agents_votes[voted_agent][voting_agent] = self.agent_2_agents_votes[voted_agent].setdefault(voting_agent, 0) + 1

                except ValueError:
                    pass
        if up_total:
            self.update_total_vote_count()
        for agent_id,dic in self.agent_2_agents_negative_talk.items():
            # reset votes count
            self.agent_2_agents_negative_talk[agent_id]= self.agent_2_agents_negative_talk.fromkeys(self.agent_2_agents_negative_talk, 0)
            self.agent_2_agents_votes[agent_id]= self.agent_2_agents_votes.fromkeys(self.agent_2_agents_votes, 0)


    def end_of_day(self):
        '''
        at the end of the day, sums all votes per agent
        :return:
        '''
        self.update_total_vote_count()

    def update_total_vote_count(self):
        for agent_id, dic in self.agent_2_prev_votes.items():
            self.agent_2_total_votes[agent_id] = sum(dic.values())
        for agent_id, dic in self.agent_2_agents_votes.items():
            self.agent_2_total_votes_curr_turn[agent_id] = sum(dic.values())
        #print(self.agent_2_total_votes)
        #print(self.agent_2_total_votes_curr_turn)

    # Knowledge = namedtuple('Knowledge', 'subject target role type reason day described_day')#Estimate
    # Vote = namedtuple('Vote', 'subject target type reason day described_day')
    # Opinion = namedtuple('Opinion', 'subject talk_number type referencedSentence day described_day')#Agree

    # TODO: Decide if when to empty certain day's messages - talk_num_2_target - in new_day func
    # TODO: ADD COMINGOUT MSG AS WELL + CHECK TYPE
    def msg_event(self, msg, talk_number):
        fields = msg._fields
        subject = msg.subject
        target = None
        if 'target' in fields:
            target = msg.target
        elif 'talk_number' in fields:
            target = self.talk_num_2_target[msg['talk_number']]
        if target is None:
            return
        role = msg.role if 'role' in fields else None
        if role is None or role == GameRoles.WEREWOLF:
            self.under_heat_value[target] = self.update_potential_vote_data(subject, target, role)