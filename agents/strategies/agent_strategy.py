from agents.information_processing.agent_perspective import *
from agents.information_processing.message_parsing import *
from agents.information_processing.sentences_container import SentencesContainer
from agents.information_processing.graph_utils.group_finder import  GroupFinder
from agents.information_processing.graph_utils.visualization import visualize
from agents.states.base_state import BaseState
from agents.information_processing.dissection.sentence_dissector import SentenceDissector
from agents.states.day_one import DayOne
from agents.information_processing.lie_detector import LieDetector
from agents.tasks.task_manager import TaskManager
from agents.vote.townsfolk_vote_model import TownsfolkVoteModel
from agents.states.state_type import StateType
from agents.strategies.player_evaluation import PlayerEvaluation
import numpy as np

# These sentences currently, don't help us much (maybe will be used in future dev).
UNUSEFUL_SENTENCES = ['Skip', 'Over']


class MessageType(Enum):
    """
    All the different message types we can receive from the server.
    TALK - Sentence has been sent by the agent.
    VOTE - The agent has given the following vote.
    EXECUTE - The agent has been executed (based on the votes).
    DEAD - The agent has been killed by the werewolves during the night.
    ATTACK_VOTE - The agent is a werewolf cooperator of ours (we will see this message only when we are in
    the werewolves group).
    FINISH - This is when the all players reveal their real identities.
    """
    TALK = 1,
    VOTE = 2,
    EXECUTE = 3,
    DEAD = 4,
    ATTACK_VOTE = 5,
    ATTACK = 6,
    WHISPER = 7,
    FINISH = 8,
    DIVINE = 9


class TownsFolkStrategy(object):
    """
    This will be  a townsfolk player strategy, we will hold a perspective for all the players in the game.
    In the case of a player of the werewolf group we need to append to this strategy another perspective that
    inspects moves of werewolves teammates through the night and day.
    """

    def __init__(self, agent_indices, my_index, role_map):
        self._perspectives = {}
        self._message_parser = MessageParser()
        self._index = my_index
        self._agent_indices = agent_indices
        self._day = 1

        # Initialize the sentences container singleton
        SentencesContainer()

        # Initialize the singleton sentences dissector.
        SentenceDissector(my_index)

        PlayerEvaluation(agent_indices, self._index)

        for idx in agent_indices:
            self._perspectives[idx] = AgentPerspective(idx, my_index,
                                                       None if idx not in role_map.keys() else role_map[idx])

        self._agent_state = DayOne(my_index, agent_indices)
        self._group_finder = GroupFinder(agent_indices + [my_index])

        self._lie_detector = LieDetector(my_index, agent_indices, role_map[str(my_index)])
        self._task_manager = TaskManager()

        self._vote_model = TownsfolkVoteModel(agent_indices, my_index)

    def update(self, diff_data):
        """
        Given the diff_data received in the agent's update function update the perspective of the agent.
        :param diff_data:
        :return:
        """
        self._group_finder.clean_groups()
        day = None
        message_type = None
        for i in range(len(diff_data.index)):
            curr_index = diff_data.loc[i, 'agent']
            agent_sentence = diff_data.loc[i, 'text']
            idx = diff_data.loc[i, 'idx']
            turn = diff_data.loc[i, 'turn']
            day = diff_data.loc[i, 'day']
            message_type = MessageType[diff_data.loc[i, 'type'].upper()]
            talk_number = TalkNumber(day, turn, idx)
            Logger.instance.write("Got sentence: " + str(agent_sentence) + " from agent " + str(curr_index)  + '\n')

            # only seer and medium players will see
            # if message_type == MessageType.DIVINE:
            #     print("DIVINE MESSAGE RECEIVED")
            #     parsed_sentence = self._message_parser.process_sentence(agent_sentence, curr_index, day,
            #                                                            talk_number)
            #     # store divined results
            #     self.update_divine_result(parsed_sentence.target, parsed_sentence.species)

            if curr_index in self._perspectives.keys():
                if agent_sentence not in UNUSEFUL_SENTENCES:
                    Logger.instance.write("Got Sentence: " + agent_sentence + '\n')
                    parsed_sentence = self._message_parser.process_sentence(agent_sentence, curr_index, day,
                                                                            talk_number)
                if message_type == MessageType.TALK:
                    if agent_sentence not in UNUSEFUL_SENTENCES:
                        self._perspectives[curr_index].update_perspective(parsed_sentence, talk_number, day)
                elif message_type == MessageType.VOTE:
                    self._perspectives[curr_index].update_vote(parsed_sentence)
                elif message_type == MessageType.EXECUTE:
                    self._perspectives[curr_index].update_status(AgentStatus.DEAD_TOWNSFOLK)
                    self._vote_model.update_dead_agent(curr_index)
                    print("AGENT" + str(self._index) + " Player " + str(curr_index) + " died by villagers")
                    PlayerEvaluation.instance.player_died(curr_index)
                elif message_type == MessageType.DEAD:
                    self._perspectives[curr_index].update_status(AgentStatus.DEAD_WEREWOLVES)
                    self._vote_model.update_dead_agent(curr_index)
                    self.update_votes_after_death(curr_index)

                elif message_type == MessageType.ATTACK_VOTE:
                    print("Got attack vote when I am in townsfolk, BUG.")
                elif message_type == MessageType.WHISPER:
                    print("Got whisper when I am in townsfolk, BUG.")
                elif message_type == MessageType.FINISH:
                    self._perspectives[curr_index].update_real_role(parsed_sentence.role)
                    self._group_finder.set_player_role(curr_index, parsed_sentence.role)
                self._perspectives[curr_index].switch_sides(day)
                self._perspectives[curr_index].log_perspective()

            else:
                # This is my index, save my own sentences if we need to reflect them in the future.
                self._message_parser.add_my_sentence(self._index, agent_sentence, day, talk_number)

        game_graph = self._group_finder.find_groups(self._perspectives, day)
        # game_graph.log()


        # If there is new data, check if new tasks can be created.
        if len(diff_data.index) > 0:
            tasks = self.generate_tasks(day)
            self._task_manager.add_tasks(tasks)
            self._task_manager.update_tasks_importance(day)

            # Make sure we update the day of the game, used for discounting.
            self._day = day


        self.update_state()

        # Note: In case you try running several games together you cant use the visualization.
        if message_type == MessageType.FINISH:
            visualize(game_graph)
            SentencesContainer.instance.clean()

    def update_votes_after_death(self, idx):
        """
        After the death of some agent we wish to update the scores in our voter model.
        :param idx:
        :return:
        """
        PlayerEvaluation.instance.player_died_werewolf(idx)
        game_graph =  self._group_finder.find_groups(self._perspectives, self._day)
        #updated_scores = analyze_death(idx, game_graph, self._vote_model.get_vottable_agents())


        updated_scores = game_graph.get_players_voting_scores()
        for agent_idx, score in updated_scores.items():
            self._vote_model.update_vote(agent_idx, score, self._day)

    def talk(self):
        """
        :return:
        """
        sentence =  self._agent_state.talk(self._task_manager)
        Logger.instance.write("I Said: " + sentence)
        return sentence

    def generate_tasks(self, day):
        """
        This is the base method of generating tasks that will help us decide what to say in the next calls
        to the talk function.
        All players with special roles such as BodyGuard, Seer and Medium are expected to override this method
        and extending it by adding specific tasks which are relevant to the added information they can gain
        using their special abilities.
        :param day:
        :return:
        """
        return self._lie_detector.find_matching_admitted_roles(self._perspectives, day)


    def update_state(self):
        """
        Update the state of the agent throughout the game, this will help us choose which tasks to do
        at given moments.
        :return:
        """
        if self._day > 1 and self._agent_state.get_type() == StateType.DAY_ONE:
            Logger.instance.write("Updated state to Base State from Day One State")
            self._agent_state = BaseState(self._index, self._agent_indices)

    def vote(self):
        return self._vote_model.get_vote(self._day)



class SeerStrategy(TownsFolkStrategy):

    def __init__(self, agent_indices, my_index, role_map, statusMap, player_perspective):
        super().__init__(agent_indices, my_index, role_map)

        self.my_index = my_index
        self._divined_agents = {}

        self.is_first_day = True

        # create prospect map {agent Idx -> suspicious score}
        self._divine_prospects = {}
        my_index_str = str(my_index)
        for agent in statusMap.keys():
            if (agent != my_index_str):
                self._divine_prospects[agent] = 0

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
        # if first day no prior knowledge -> random divine
        if self.is_first_day:
            ls = list(self._divine_prospects.keys())
            idx = np.random.randint(0, len(ls))

            return ls[idx]

        # use prior knowledge to update prospect list
        for agent in self._divine_prospects:
            score = 0
            agent_idx = int(agent)
            if self._perspectives[agent_idx]._status == AgentStatus.DEAD_WEREWOLVES:
                # If was attacked then definitly NOT a werewolf (if possessed then seer can't know anyhow)
                if agent not in self._divined_agents:
                    self.update_divine_result(agent, 'HUMAN')

        # decide
        agent_to_divine = max(self._divine_prospects.keys(), key=(lambda key: self._divine_prospects[key]))

        return str(agent_to_divine)

    def talk(self):
        pass


'''
for each agent in prospects:
    look at perspective :
        agent status:
            if dead then remove from prospects.
        
        liar score 0.3
        admitted role 0.2
        likely role 0.25
        check if a known werewolf in cooperators 0.4

        each day:
            0.4 * prev score + 0.6 * current score 
'''