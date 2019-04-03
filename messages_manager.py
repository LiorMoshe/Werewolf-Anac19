import pandas as pd

class MessageManager(object):
    def __init__(self, self_idx, num_agents):
        self.messages = {}
        for agent_idx in range(num_agents):
            if self_idx == agent_idx:
                continue
            self.messages[agent_idx] = []

    def add_messages(self, game_diff):
        print(game_diff)
        game_diff_msgs = game_diff["text"]
        for idx, agent in enumerate(game_diff["agent"]):
            self.messages[agent].append(game_diff_msgs[idx])
            print(game_diff_msgs[idx])

    def update_base_info(self, base_info):
        pass


