from agents.information_processing.agent_perspective import *
from agents.information_processing.message_parsing import *
from agents.information_processing.sentences_container import SentencesContainer
from agents.information_processing.graph_utils.group_finder import GroupFinder
from agents.information_processing.graph_utils.visualization import visualize
from agents.states.base_state import BaseState
from agents.information_processing.dissection.sentence_dissector import SentenceDissector
from agents.states.day_one import DayOne
from agents.states.night_one import Night_one
from agents.information_processing.lie_detector import LieDetector
from agents.tasks.task_manager import TaskManager
from agents.vote.wolf_vote_model import wolfVoteModel
from agents.states.state_type import StateType
from agents.strategies.player_evaluation import PlayerEvaluation
from agents.strategies.role_estimations import RoleEstimations
from agents.tasks.task_type import TaskType
from agents.tasks.request_attack_task import RequestAttackTask
from agents.tasks.fake_role_task import FakeRoleTask
import numpy as np
from agents.strategies.agent_strategy import TownsFolkStrategy
from agents.game_roles import GameRoles
import operator
from agents.sentence_generators.logic_generators import *

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


class WolfStrategy(TownsFolkStrategy):
    """
    This will be  a townsfolk player strategy, we will hold a perspective for all the players in the game.
    In the case of a player of the werewolf group we need to append to this strategy another perspective that
    inspects moves of werewolves teammates through the night and day.
    """

    def __init__(self, agent_indices, my_index, role_map, player_perspective):
        self._humans = [i for i in agent_indices if not str(i) in role_map.keys()]
        self._wolves = [i for i in role_map.keys()]
        self.fake_rol = None
        if len(agent_indices) > 5:
            self._agent_night_state = Night_one(my_index, agent_indices)
        else:
            self.fake_rol = np.random.choice(['SEER', 'VILLAGER'])
        self._agent_state = DayOne(my_index, agent_indices)
        #self.fake_rol = None
        self.fake_role_tasks = agent_indices.copy()
        self._message_parser = MessageParser()
        self._index = my_index
        self._agent_indices = agent_indices
        self._day = 0
        self._role = role_map[str(self._index)]
        self._player_perspective = player_perspective
        self.come_out_role = False
        self.flag = True

        # Used for tasks that can be done only once per day.
        self._done_in_day = False

        # Initialize the sentences container singleton
        SentencesContainer()

        # Initialize the singleton sentences dissector.
        SentenceDissector(my_index) #TODO: check!

        PlayerEvaluation(agent_indices, self._index, self._wolves)

        RoleEstimations(self._agent_indices, self._index)

        self._perspectives = {}
        self._teammates = {}

        for idx in self._agent_indices:
            self._perspectives[idx] = AgentPerspective(idx, my_index, len(agent_indices) + 1,
                                                       None if idx not in role_map.keys() else role_map[idx])
        for idx in self._agent_indices:
            self._teammates[idx] = AgentPerspective(idx, my_index, len(agent_indices) + 1,
                                                   None if idx not in role_map.keys() else role_map[idx])

        self._group_finder = GroupFinder(agent_indices + [my_index], my_index)

        self._lie_detector = LieDetector(my_index, agent_indices, role_map[str(my_index)])
        self._night_task_manager = TaskManager()
        self._task_manager = TaskManager()

        self._vote_model = wolfVoteModel(self._perspectives, self._wolves, my_index)
        self._special_roles = {}
        self._werewolf_accused_counter = 0
        self._enemies = {i: 0 for i in self._humans}
        self._enemies_quoats = {i: "" for i in self._humans}
        self._enemies_substr = "VOTE Agent[{0:02d}]".format(self._index)
        self._accusing = {i: "" for i in self._humans}
        self._accusing_substrs = ["DIVINED Agent[{0:02d}] WEREWOLF".format(self._index),
                                 "ESTIMATE Agent[{0:02d}] WEREWOLF".format(self._index)]


    def update(self, diff_data, request):
        """
        Given the diff_data received in the agent's update function update the perspective of the agent.
        :param diff_data:
        :return:
        """
        """
                Given the diff_data received in the agent's update function update the perspective of the agent.
                :param diff_data:
                :return:
                """
        #self._group_finder.clean_groups()
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
            Logger.instance.write("Got sentence: " + str(agent_sentence) + " from agent " + str(curr_index) + '\n')

            if curr_index in self._perspectives.keys():
                if agent_sentence not in UNUSEFUL_SENTENCES:
                    Logger.instance.write("Got Sentence: " + agent_sentence + '\n')
                    parsed_sentence = self._message_parser.process_sentence(agent_sentence, curr_index, day,
                                                                            talk_number)
                if message_type == MessageType.TALK:
                    if agent_sentence not in UNUSEFUL_SENTENCES:
                        self._perspectives[curr_index].update_perspective(parsed_sentence, talk_number, day)
                        if parsed_sentence.type == SentenceType.COMINGOUT:
                            if parsed_sentence.target == parsed_sentence.subject:
                                admitted_role = parsed_sentence.role
                                if admitted_role == self.fake_rol and not self.come_out_role:
                                    self.come_out_role = True
                elif message_type == MessageType.VOTE:
                    self._perspectives[curr_index].update_vote(parsed_sentence)
                elif message_type == MessageType.EXECUTE:
                    self._perspectives[curr_index].update_status(AgentStatus.DEAD_TOWNSFOLK)
                    self._teammates[curr_index].update_status(AgentStatus.DEAD_TOWNSFOLK)
                    self._vote_model.update_dead_agent(curr_index)
                    print("AGENT" + str(self._index) + " Player " + str(curr_index) + " died by villagers")
                    PlayerEvaluation.instance.player_died(curr_index)
                    if curr_index in self._enemies:
                        del self._enemies[curr_index]
                    if curr_index in self._accusing:
                        del self._accusing[curr_index]
                    if curr_index in self._humans:
                        self._humans.remove(curr_index)
                    elif curr_index in self._wolves:
                        self._wolves.remove(curr_index)
                elif message_type == MessageType.DEAD:
                    self._perspectives[curr_index].update_status(AgentStatus.DEAD_WEREWOLVES)
                    self._teammates[curr_index].update_status(AgentStatus.DEAD_WEREWOLVES)
                    self._vote_model.update_dead_agent(curr_index)
                    self.update_votes_after_death(curr_index)
                    if curr_index in self._enemies:
                        del self._enemies[curr_index]
                    if curr_index in self._accusing:
                        del self._accusing[curr_index]
                    if curr_index in self._humans:
                        self._humans.remove(curr_index)
                    elif curr_index in self._wolves:
                        self._wolves.remove(curr_index)

                elif message_type == MessageType.ATTACK_VOTE:#TODO
                    self._teammates[curr_index].update_vote(parsed_sentence)
                elif message_type == MessageType.WHISPER:
                    if agent_sentence not in UNUSEFUL_SENTENCES:
                        self._teammates[curr_index].update_perspective(parsed_sentence, talk_number, day,save_sen=False)

                elif message_type == MessageType.FINISH:
                    self._perspectives[curr_index].update_real_role(parsed_sentence.role)
                    #self._group_finder.set_player_role(curr_index, parsed_sentence.role)

                self._perspectives[curr_index].switch_sides(day)
            else:
                # This is my index, save my own sentences if we need to reflect them in the future.
                self._message_parser.add_my_sentence(self._index, agent_sentence, day, talk_number)


        game_graph = self._group_finder.find_groups(self._perspectives, day) #TODO
        # If there is new data, check if new tasks can be created.
        if len(diff_data.index) > 0:
            self.handle_estimations(game_graph)
            tasks = self.generate_tasks(game_graph, day)
            for t in tasks:
                if t.get_type() == TaskType.SAME_ADMITTED_ROLE:
                    self._night_task_manager.add_task(t)
            self._task_manager.add_tasks(tasks)
            self._task_manager.update_tasks_importance(day)
            self._night_task_manager.update_tasks_importance(day)

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
            #self._vote_model.clear_scores()
            self._done_in_day = False

        elif request == "VOTE":
            PlayerEvaluation.instance.log()
            updated_scores = game_graph.get_players_voting_scores()
            for agent_idx, score in updated_scores.items():
                self._vote_model.update_vote(agent_idx, score)


    def generate_talk(self):
        """
        :return:
        """
        if self.come_out_role and self.flag:
            self.flag = False
            if self.fake_rol == GameRoles.MEDIUM or self.fake_rol == GameRoles.SEER:
                return "COMINGOUT Agent[{me}] {rol}". \
                    format(rol=self.fake_rol, me=str(self._index))
        # return "BECAUSE (DAY 1 (DIVINED Agent[05] WEREWOLF)) (ESTIMATE Agent[01] WEREWOLF)"
        max_accusing_value = 1
        if self._werewolf_accused_counter > max_accusing_value:
            top_accusing = max(self._accusing, key=self._accusing.get)
            if self._accusing[top_accusing]:
                sentence = "BECAUSE ({accusing_sentence}) (REQUEST ANY (ESTIMATE Agent[{0:02d}] WEREWOLF))".\
                    format(top_accusing, accusing_sentence=self._accusing[top_accusing])
                Logger.instance.write("I Said: " + sentence)
                self._accusing[top_accusing] = ""
                self._werewolf_accused_counter = 0
                return sentence

        max_heat_value = 10
        if self._player_perspective.under_heat_value[self._index] > max_heat_value:
            worst_enemy = max(self._enemies, key=self._enemies.get)
            if self._enemies[worst_enemy] and self._enemies_quoats[worst_enemy]:
                self._player_perspective.under_heat_value[self._index] -= 8
                sentence = "BECAUSE ({accusing_sentence}) (REQUEST ANY (VOTE Agent[{0:02d}]))".\
                    format(worst_enemy, accusing_sentence=self._enemies_quoats[worst_enemy])
                Logger.instance.write("I Said: " + sentence)
                return sentence

        else:
            sentence = self._agent_state.talk(self._task_manager)
            Logger.instance.write("I Said: " + sentence)
            return sentence

    def digest_sentences(self, diff_data):
        for i, row in diff_data.iterrows():
            talking_agent_idx = row["agent"]
            if talking_agent_idx != self._index and talking_agent_idx not in self._wolves:
                # check if i'm under attack - agents are trying to vote me out
                substr = self._enemies_substr
                if "REQUEST" in row["text"] and substr in row["text"]:
                    Logger.instance.write(str(talking_agent_idx) + "WANTED TO VOTE ME")
                    print(talking_agent_idx, "WANTED TO VOTE ME")
                    self._player_perspective.under_heat_value[self._index] += 1
                    if talking_agent_idx in self._enemies.keys():
                        self._enemies[talking_agent_idx] += 1
                        self._enemies_quoats[talking_agent_idx] = "DAY {day} ({substr})".format(day=str(self._day),
                                                                                                substr=substr)
                    self._vote_model.set_to_max_score(talking_agent_idx)

                # if people view me as a werewolf
                substrs = self._accusing_substrs
                for substr in substrs:
                    if substr in row["text"]:
                        Logger.instance.write(str(talking_agent_idx) + "CALLED ME WOLF")
                        print(talking_agent_idx, "CALLED ME WOLF")
                        self._player_perspective.under_heat_value[self._index] += 1
                        self._werewolf_accused_counter += 1
                        if talking_agent_idx in self._enemies.keys():
                            self._enemies[row["agent"]] += 1
                        if talking_agent_idx in self._accusing.keys():
                            self._accusing[talking_agent_idx] = "DAY {day} ({substr})".format(day=str(self._day),
                                                                                              substr=substr)
                        self._vote_model.set_to_max_score(talking_agent_idx)

    def get_next_attck(self):
        self._day += 1
        self._night_task_manager._pop_all()
        self._task_manager._pop_all()
        if self.come_out_role and (self.fake_rol == GameRoles.SEER or self.fake_rol == GameRoles.MEDIUM):
            temp = np.random.choice(self.fake_role_tasks)
            self.fake_role_tasks.remove(temp)
            if temp in self._wolves:
                frind = True
            else:
                frind = np.random.choice([False,True],p=[0.4,0.6])
            t = FakeRoleTask(temp,1000,self._day,[self._index],self._index,self.fake_rol,frind)
            self._task_manager.add_task(t)
        team_attack = self.get_best_attak_for_team()
        team_risk = 0.5
        my_attack = max(self._enemies.items(), key=operator.itemgetter(1))[0]
        my_risk = 0.35
        spichel_attack = np.random.choice(self._humans)
        random_risk = 0.15
        return np.random.choice([my_attack, team_attack,spichel_attack], p=[my_risk, team_risk,random_risk])
    #
    # def get_bff(self):
    #     vote_for = self.get_best_vote_opt()
    #
    #     score = 1  # get_risk(vote_for)
    #     vote_for_bff = np.max((s, coop) for s, coop in
    #                           self._strategy._perspectives[vote_for].get_closest_cooperators(self._base_info._day) if
    #                           coop not in self._base_info._role_map)[1]
    #     vote_avrg_max_evel = 1  # get_avrg_obsical()

    def whisper(self):
        """
        :return:
        """
        if self.fake_rol == None:
            self.fake_rol = np.random.choice(['SEER','VILLAGER','MEDIUM'])
            return "COMINGOUT Agent[{me}] {rol}".\
                    format(rol=self.fake_rol,me=str(self._index))
        new_kill_task = RequestAttackTask(max(self._enemies.items(), key=operator.itemgetter(1))[0],1000,self._day,[self._index],self._index)
        self._night_task_manager.add_task(new_kill_task)
        sentence = self._agent_night_state.talk(self._night_task_manager)
        Logger.instance.write("I Said: " + sentence)
        return sentence

    def update_night_state(self):
        """
        Update the state of the agent throughout the game, this will help us choose which tasks to do
        at given moments.
        :return:
        """
        if self._day > 0 and self._agent_night_state.get_type() == StateType.NIGHT_ONE:
            Logger.instance.write("Updated night state to Base State from Day One State")
            self._agent_night_state = BaseState(self._index, self._agent_indices)

    def get_best_attak_for_team(self):
        eneamy = {}
        for cop,cop_persp in self._teammates.items():
            temp = cop_persp.get_enemies()
            for id,t_enemy in temp.items():
                eneamy[id] = eneamy.get(id,0) + t_enemy.get_hostility(self._day)
        return max(eneamy.items(), key=operator.itemgetter(1))[0]
