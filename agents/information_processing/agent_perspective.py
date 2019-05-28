from enum import Enum
from agents.logger import Logger
from agents.information_processing.dissection.sentence_dissector import SentenceDissector
from agents.information_processing.dissection.player_representation import Cooperator, Enemy


MIN_SEVERITY_VAL = 1
MAX_SEVERITY_VAL = 3

class AgentStatus(Enum):
    ALIVE = 1
    DEAD_TOWNSFOLK = 2,
    DEAD_WEREWOLVES = 3


class AgentPerspective(object):
    """
    Contains information about specific agent in the game.
    Agent Index: Index of this agents.
    Liar Score: Based on information given throughout the game a score whether this agent
    is a truth teller or a liar.
    Admitted role: Role that the agent stated that he has, paired with the sentence in which he said he has
    that role.
    Likely cooperators: The agents that are likely to cooperate with this agent.
    Likely non-cooperators: The agents that this agent doesn't cooperate with, he showed disagreement to them.
    Likely Role: The role I think that player has based on what happened thus far.
    Status: Status of the agent, is he alive or dead, if he is dead, who killed him? The townsfolk or the
    werewolves.
    TODO- If it's easier to be hostile, should everyone start as cooperator.
    """

    def __init__(self, agent_idx, my_idx, role=None):
        """
        :param agent_idx: Index of this agent.
        :param my_idx: Index of our agent.
        :param sentences_container Container that maps talk number to a processed sentence.
        :param player_perspective
        :param role Role of the player if we know it from the role_map.
        """
        self._index = agent_idx
        self.my_agent = my_idx
        self._liar_score = 0.0
        self._cooperators = {}
        self._noncooperators = {}
        self._admitted_role = None
        self._likely_role = None
        self._status = AgentStatus.ALIVE
        self._role = role
        self._vote_score = 0
        # Messages ordered by day that are directed to me (think these are only inquire and request messages).
        self.messages_to_me = {}

    def get_index(self):
        return self._index

    def update_status(self, status):
        self._status = status

    def update_real_role(self, role):
        self._role = role

    def get_admitted_role(self):
        return self._admitted_role

    def get_messages_to_me(self, day):
        """
        Get messages that were directed to my agent on a given day.
        :param day:
        :return:
        """
        return self.messages_to_me[day]

    def switch_sides(self, day):
        """
        Go over all the cooperators and non cooperators and check if all of them have a positive value of
        fondness of hostility. If one of them has a negative value it means that it switched sides.
        :param day
        :return:
        """
        for index, cooperator in self._cooperators.items():
            total_fondness = self._cooperators[index].get_fondness(day)
            if total_fondness <= 0:
                Logger.instance.write("Agent " + str(index) + " switch sides! Cooperator to enemy.")
                self._noncooperators[index] = self._cooperators[index].convert_to_enemy()
                self._cooperators.pop(index, None)

        for index, enemy in self._noncooperators.items():
            total_hostility = self._noncooperators[index].get_hostility(day)
            if total_hostility <= 0:
                Logger.instance.write("Agent " + str(index) + " switched sides! Enemy to cooperator.")
                self._cooperators[index] = self._noncooperators[index].convert_to_cooperator()
                self._noncooperators.pop(index, None)



    def add_message_directed_to_me(self, dissected_sentence):
        """
        Save messages such as requests or inquires which are directed towards our agent.
        In the case of a request the subject requires from the target to act according to the request.
        In the case of inquire if there is no mention of ANY the subject only wants to know whether the
        target agrees or not, if there is ANY we expect the target to replace the ANY with his answers.
        :param dissected_sentence
        :return:
        """
        if dissected_sentence.day in self.messages_to_me.keys():
            self.messages_to_me[dissected_sentence.day].append(dissected_sentence)
        else:
            self.messages_to_me[dissected_sentence.day] = [dissected_sentence]


    def update_perspective(self, message, talk_number, day):
        """
        Given a new message update my perspective.
        :param message:
        :param talk_number
        :param day
        :return:
        """

        Logger.instance.write("Dissecting Message: " + str(message))

        result = SentenceDissector.instance.dissect_sentence(message, talk_number, day)

        if result.is_hostile():
            self.update_enemy(result.enemy)
        elif result.cooperator is not None:
            self.update_cooperator(result.cooperator)
        else:
            Logger.instance.write("[AGENT " + str(self._index) + "]: Got sentence " + str(message) + " but found" +
                                  " nothing major while trying to dissect it.")

        if result.directed_to_me:
            self.add_message_directed_to_me(result)

        if result.admitted_role is not None:
            self._admitted_role = result.admitted_role

    def update_cooperator(self, cooperator):
        if cooperator.index in self._cooperators.keys():
            Logger.instance.write("[AGENT " + str(self._index) + "]: Updating cooperator: " + str(cooperator.index))
            self._cooperators[cooperator.index].merge_cooperators(cooperator)
        elif cooperator.index in self._noncooperators.keys():
            self.update_enemy(cooperator.convert_to_enemy())
        else:
            Logger.instance.write("[AGENT " + str(self._index) + "]: Adding a new cooperator: " + str(cooperator.index))
            self._cooperators[cooperator.index] = cooperator

    def update_enemy(self, enemy):
        if enemy.index in self._noncooperators.keys():
            Logger.instance.write("[AGENT " + str(self._index) + "]: Updating enemy: " + str(enemy.index))
            self._noncooperators[enemy.index].merge_enemies(enemy)
        elif enemy.index in self._cooperators.keys():
            self.update_cooperator(enemy.convert_to_cooperator())
        else:
            Logger.instance.write("[AGENT " + str(self._index) + "]: Adding a new enemy: " + str(enemy.index))
            self._noncooperators[enemy.index] = enemy


    def update_vote(self, vote):
        """
        Update cooperators and enemies based on vote of the agent. A vote will get a high value
        of hostility because it means this agent wants the  other one dead.
        :param vote:
        :return:
        """
        enemy = Enemy(vote.target, history={}).update_hostility(hostility=4, message=vote)
        self.update_enemy(enemy)

    def get_cooperators(self):
        return list(self._cooperators.keys())

    def get_enemies(self):
        return list(self._noncooperators.keys())

    def lie_detected(self):
        """
        In case a lie was detected we will increment the liar score of this agent, it is more likely that
        he is a liar.
        :return:
        """
        self._liar_score += 1

    def log_perspective(self):
        Logger.instance.write("Logging perspective of agent: " + str(self._index))
        for idx, cooperator in self._cooperators.items():
            Logger.instance.write(str(cooperator))

        for idx, enemy in self._noncooperators.items():
            Logger.instance.write(str(enemy))

    def update_vote_score(self, value):
        if abs(value) < MIN_SEVERITY_VAL or abs(value) > MAX_SEVERITY_VAL:
            assert "Vote score value is out of bound"
        self._vote_score += value
