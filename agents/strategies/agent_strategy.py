from agents.information_processing.agent_perspective import *
from agents.information_processing.message_parsing import *
from agents.information_processing.sentences_container import SentencesContainer
from agents.information_processing.graph_utils.group_finder import  GroupFinder
from agents.states.base_state import BaseState
from agents.information_processing.dissection.sentence_dissector import SentenceDissector
from agents.states.day_one import DayOne
from agents.information_processing.lie_detector import LieDetector
from agents.tasks.task_manager import TaskManager
from agents.vote.townsfolk_vote_model import TownsfolkVoteModel
from agents.states.state_type import StateType
from agents.strategies.player_evaluation import PlayerEvaluation
from agents.strategies.role_estimations import RoleEstimations
from agents.tasks.guard_task import GuardTask
from agents.tasks.vote_task import VoteTask
from agents.tasks.divine_task import DivineTask
from agents.tasks.identify_task import IdentifyTask
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
    DIVINE = 9,
    IDENTIFY = 10,
    GUARD = 11

class TownsFolkStrategy(object):
    """
    This will be  a townsfolk player strategy, we will hold a perspective for all the players in the game.
    In the case of a player of the werewolf group we need to append to this strategy another perspective that
    inspects moves of werewolves teammates through the night and day.
    """

    def __init__(self, agent_indices, my_index, role_map, player_perspective):
        self._perspectives = {}
        self._message_parser = MessageParser()
        self._index = my_index
        self._agent_indices = agent_indices
        self._day = 1
        self._role = role_map[str(self._index)]
        self._player_perspective = player_perspective

        # Used for tasks that can be done only once per day.
        self._done_in_day = False

        # Initialize the sentences container singleton
        SentencesContainer()

        # Initialize the singleton sentences dissector.
        SentenceDissector(my_index)

        PlayerEvaluation(agent_indices, self._index)

        RoleEstimations(self._agent_indices, self._index)

        for idx in agent_indices:
            self._perspectives[idx] = AgentPerspective(idx, my_index, len(agent_indices) + 1,
                                                       None if idx not in role_map.keys() else role_map[idx])

        self._agent_state = DayOne(my_index, agent_indices)
        self._group_finder = GroupFinder(agent_indices + [my_index], my_index)

        self._lie_detector = LieDetector(my_index, agent_indices, role_map[str(my_index)])
        self._task_manager = TaskManager()

        self._vote_model = TownsfolkVoteModel(agent_indices, my_index)

        # Save here all players with special roles we currently trust.
        self._special_roles = {}

    def handle_message(self, message, game_graph):
        """
        Given a message directed towards our agent decide whether we should handle it in some form.
        It can be either by adjusting weights in our voter model or in the form of a future task.
        This is only relevant to request or inquires.
        We only handle inquires and requests relevant for villagers, meaning questions like who we votes
        for and can we do some special action won't be answered.
        :param message:
        :param game_graph
        :return:
        """
        tasks = []
        try:
            if message.type == SentenceType.REQUEST:
                Logger.instance.write("GOT REQUEST MESSAGE TO ME " + str(message.original_message))
                if message.content.type == SentenceType.VOTE:
                    self._vote_model.handle_vote_request(game_graph, message.subject, message.content.target)


            elif message.type == SentenceType.INQUIRE:
                Logger.instance.write("GOT REQUEST MESSAGE TO ME " + str(message.original_message))
                if message.content.type == SentenceType.VOTE and message.content.target == "ANY":
                    if message.subject in game_graph.get_node(self._index).get_top_k_cooperators(k=3):
                        target = self._vote_model.get_vote()
                        tasks.append(VoteTask(1, self._day, [target], self._index, target))
        except:
            print("VILLAGER HANDLE MESSAGE ERR ")
        return tasks



    def handle_messages_to_me(self, game_graph):
        """
        Go over all the perspectives of agents and collect messages directed to me on a given day
        and decide which ones are going to be handled as further tasks.
        :param game_graph
        :return:
        """
        tasks = []
        try:
            for idx, perspective in self._perspectives.items():
                messages_to_me = perspective.get_and_clean_messages_to_me(self._day)
                for message in messages_to_me:
                    tasks += self.handle_message(message, game_graph)
        except:
            print("VILLAGER HANDLE MESSAGE ERR ")
        return tasks

    def update(self, diff_data, request):
        """
        Given the diff_data received in the agent's update function update the perspective of the agent.
        :param diff_data:
        :return:
        """
        try:
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

                #only seer and medium players will see
                if message_type == MessageType.DIVINE or message_type == MessageType.IDENTIFY:
                    print("DIVINE MESSAGE RECEIVED")
                    parsed_sentence = self._message_parser.process_sentence(agent_sentence, curr_index, day,
                                                                            talk_number)
                    # store divined results
                    self.update_divine_result(parsed_sentence.target, parsed_sentence.species)

                if curr_index in self._perspectives.keys():
                    if agent_sentence not in UNUSEFUL_SENTENCES:
                        Logger.instance.write("Got Sentence: " + agent_sentence + '\n')
                        parsed_sentence = self._message_parser.process_sentence(agent_sentence, curr_index, day,
                                                                                talk_number)
                    if message_type == MessageType.TALK:
                        if agent_sentence not in UNUSEFUL_SENTENCES:
                            self._perspectives[curr_index].update_perspective(parsed_sentence, talk_number, day)
                            player_perspective_msg_types = [SentenceType.COMINGOUT, SentenceType.AGREE, SentenceType.ESTIMATE, SentenceType.VOTE]
                            if parsed_sentence.type in player_perspective_msg_types or\
                                (parsed_sentence.type in [SentenceType.REQUEST, SentenceType.INQUIRE] and parsed_sentence.content.type in player_perspective_msg_types):
                                if parsed_sentence.target not in self._perspectives:
                                    non_coop = 0
                                else:
                                    non_coop = self._perspectives[int(parsed_sentence.target)].get_non_coop_count()
                                self._player_perspective.msg_event(parsed_sentence, talk_number, non_coop)
                            elif "COMINGOUT" in agent_sentence or "ESTIMATE" in agent_sentence or "VOTE" in agent_sentence:
                                for sentence in parsed_sentence.sentences:
                                    if sentence.type in player_perspective_msg_types:
                                        if sentence.target not in self._perspectives:
                                            non_coop = 0
                                        else:
                                            non_coop = self._perspectives[int(sentence.target)].get_non_coop_count()
                                        self._player_perspective.msg_event(sentence, talk_number, non_coop)
                                        break

                    elif message_type == MessageType.VOTE:
                        self._perspectives[curr_index].update_vote(parsed_sentence)
                        if parsed_sentence.target not in self._perspectives:
                            non_coop = 0
                        else:
                            non_coop = self._perspectives[int(parsed_sentence.target)].get_non_coop_count()
                        self._player_perspective.msg_event(parsed_sentence, talk_number, non_coop)
                    elif message_type == MessageType.EXECUTE:
                        if curr_index == self._index:
                            self._player_perspective.update_my_status(AgentStatus.DEAD_TOWNSFOLK)
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
                else:
                    # This is my index, save my own sentences if we need to reflect them in the future.
                    self._message_parser.add_my_sentence(self._index, agent_sentence, day, talk_number)


            game_graph = self._group_finder.find_groups(self._perspectives, day)
            #self._player_perspective.update_relationships(game_graph)

            # If there is new data, check if new tasks can be created.
            if len(diff_data.index) > 0:
                self.handle_estimations(game_graph)
                tasks = self.generate_tasks(game_graph, day)
                self._task_manager.add_tasks(tasks)
                self._task_manager.update_tasks_importance(day)

                # Make sure we update the day of the game, used for discounting.
                self._day = day


            self.update_state()
            self.update_roles()

            # Note: In case you try running several games together you cant use the visualization.
            if message_type == MessageType.FINISH:
                # visualize(game_graph)
                SentencesContainer.instance.clean()
                PlayerEvaluation.instance.reset(self._agent_indices, self._index)
                RoleEstimations.instance.reset(self._agent_indices, self._index)

            # At the end of the day reset the scores accumulated by the vote model.
            if request == "DAILY_FINISH":
                self._vote_model.clear_scores()
                self._done_in_day = False

            elif request == "VOTE":
                PlayerEvaluation.instance.log()
                updated_scores = game_graph.get_players_voting_scores()
                for agent_idx, score in updated_scores.items():
                    self._vote_model.update_vote(agent_idx, score)
        except:
            print("AGENT STRATEGY EXCEPTION IN UPDATE:")


    def update_votes_after_death(self, idx):
        """
        After the death of some agent we wish to update the scores in our voter model.
        :param idx:
        :return:
        """
        PlayerEvaluation.instance.player_died_werewolf(idx)

    def update_roles(self):
        """
        Update the special roles of players tracked through the game, if a player lied remove him
        from our mapping otherwise add his new role to the mapping
        :return:
        """
        try:
            for idx, perspective in self._perspectives.items():
                admitted_role = perspective.get_admitted_role()
                if perspective.get_liar_score() == 0 and admitted_role is not None:
                    self._special_roles[admitted_role["role"]] = idx
                elif perspective.get_liar_score() > 0 and admitted_role["role"] in self._special_roles:
                    del self._special_roles[admitted_role["role"]]
        except:
            print("VILLAGER HANDLE MESSAGE ERR ")



    def handle_estimations(self, game_graph):
        """
        If players with special roles that I can trust have some estimations adjust my
        evaluation of other players
        :param game_graph
        :return:
        """
        try:
            for idx, perspective in self._perspectives.items():

                if perspective.get_status() == AgentStatus.ALIVE and perspective.has_estimations():

                        estimations = perspective.get_estimations()


                        Logger.instance.write("Checking estimations of Agent" + str(idx))
                        if idx in game_graph.get_node(self._index).get_top_k_cooperators(k=3):
                            Logger.instance.write("Agent" + str(self._index) + " is a cooperator, listening to estimations: " + str(estimations))
                            for agent_idx, estimation in estimations.items():
                                if estimation == "WEREWOLF":
                                    PlayerEvaluation.instance.player_is_werewolf(agent_idx)
                                elif estimation == "HUMAN":
                                    PlayerEvaluation.instance.player_in_townsfolk(agent_idx)
        except:
            print("VILLAGER HANDLE MESSAGE ERR ")

    def talk(self):
        """
        :return:
        """
        try:
            sentence =  self._agent_state.talk(self._task_manager)
            Logger.instance.write("I Said: " + sentence)
            return sentence
        except:
            print("VILLAGER HANDLE MESSAGE ERR ")
            return "Skip"

    def generate_tasks(self, game_graph, day):
        """
        This is the base method of generating tasks that will help us decide what to say in the next calls
        to the talk function.
        All players with special roles such as BodyGuard, Seer and Medium are expected to override this method
        and extending it by adding specific tasks which are relevant to the added information they can gain
        using their special abilities.
        :param game_graph
        :param day:
        :return:
        """
        try:
            tasks = self._lie_detector.find_matching_admitted_roles(self._perspectives, day)

            tasks += self.handle_messages_to_me(game_graph)

            if not self._done_in_day:
                request_vote_task = PlayerEvaluation.instance.update_evaluation(game_graph, day)

                if request_vote_task is not None:
                    tasks.append(request_vote_task)

                if "BODYGUARD" in self._special_roles and self._role != "BODYGUARD":
                    print("Creating bodyguard task")

                    tasks.append(GuardTask.generate_guard_task(game_graph, self._index, self._special_roles["BODYGUARD"],
                                                               PlayerEvaluation.instance.players_alive(), 1, self._day))

                if "SEER" in self._special_roles and self._role != "SEER":
                    print("Creating seer task")

                    tasks.append(DivineTask.generate_divine_task(self._index, self._special_roles["SEER"], 1, self._day))

                if "MEDIUM" in self._special_roles and self._role != "MEDIUM" and PlayerEvaluation.instance.get_last_dead() is not None:
                    tasks.append(IdentifyTask(1, self._day, [self._special_roles["MEDIUM"], PlayerEvaluation.instance.get_last_dead()],
                                              self._index, self._special_roles["MEDIUM"], PlayerEvaluation.instance.get_last_dead()))



                self._done_in_day = True
        except:
            print("ERROR WOLF STRATEGY UPDATE")
        return tasks




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
        try:
            Logger.instance.write("Voting on day " + str(self._day))
            result = self._vote_model.get_vote()
            Logger.instance.write("Voted for Agent" + str(result))
            return result
        except:
            try:
                min = np.inf
                id = 1
                for k,v in self._vote_model._vote_scores.items():
                    if v < min:
                        id = k
                        min = v
                return int(id)
            except:
                return int(np.random.choice(self._vote_model._vote_scores.keys()))