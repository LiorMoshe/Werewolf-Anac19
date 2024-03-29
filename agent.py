from aiwolfpy.tcpipclient_parsed import connect_parse
from agents.agent_container import AgentContainer
from agents.logger import Logger

"""
Sample of an agent based on the aiwolfpy standards.
"""


class Werewolf(object):

    def __init__(self):
        pass

    def getName(self):
        return "Werewolf"

    def initialize(self, base_info, diff_data, game_setting):
        """
        This function is called before the game starts.
        :param base_info: contains basic information available to your agent at the current state of the game.
        :param diff_data: A pandas dataframe that contains every new information since last communication with server.
        :param game_setting:contains a number of settings related to the current came as specified the AIWolf server,
        such as number of players, how many times an agent can talk per day, etc.
        :return: None
        """
        print("Initialized")

    def dayStart(self):
        print("Day Started")

    def talk(self):
        return "Skip"

    def whisper(self):
        return ""

    def vote(self):
        return ""

    def attack(self):
        pass

    def divine(self):
        pass

    def guard(self):
        pass

    def finish(self):
        pass

    def update(self, base_info, diff_data, request):
        pass


if __name__=="__main__":
    # Sample code, how to connect to the server.
    my_agent = AgentContainer()
    connect_parse(my_agent)
    Logger.instance.close()
