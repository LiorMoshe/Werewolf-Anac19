import pandas as pd
import collections



class MessageManager(object):
    def __init__(self, self_idx, num_agents):
        self.messages = {}
        for agent_idx in range(1,num_agents+1):
            if self_idx == agent_idx:
                continue
            self.messages[agent_idx] = []
            self.self_id = self_idx

    def add_messages(self, game_diff):
        print(game_diff)
        game_diff_msgs = game_diff["text"]
        for idx, agent in enumerate(game_diff["agent"]):
            if idx+1 == self.self_id:
                continue
            self.messages[agent].append(game_diff_msgs[idx])
            print(game_diff_msgs[idx])

    def update_base_info(self, base_info):
        pass

    def create_message(self):
        message = collections.namedtuple("subject", "target", "COMINGOUT", "ESTIMATE", "Agree", "Disagree","Action",
                                         "Past Result", "Reqiest", "Because", "Inquire", "Logic Op", "Skip")
        return message