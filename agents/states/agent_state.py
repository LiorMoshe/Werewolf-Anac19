from abc import ABC, abstractmethod
import random
from agents.sentence_generators.question_pool import *
from agents.information_processing.sentences_container import SentencesContainer
from agents.game_roles import GameRoles

"""
Compare  between two sentences recursively.
"""
def compare_sentences(first_sentence, second_sentence):
    if first_sentence.type == second_sentence.type and first_sentence.subject == second_sentence.subject \
            and first_sentence.target == second_sentence.target:
        if hasattr(first_sentence, 'content'):
            return compare_sentences(first_sentence.content, second_sentence.content)
        elif hasattr(second_sentence, 'referencedSentence'):
            return compare_sentences(first_sentence.referencedSentence, second_sentence.referencedSentence)
        elif hasattr(second_sentence, 'sentences'):
            first_logic_sentences = first_sentence.sentences
            second_logic_sentences = second_sentence.sentences

            if len(first_logic_sentences) != len(second_logic_sentences):
                return False

            final_res = True
            for i in range(len(first_logic_sentences)):
                final_res &= compare_sentences(first_logic_sentences[i], second_logic_sentences[i])
            return final_res



BASE_QUESTIONS = [who_will_vote_for, do_you_estimate, do_you_comingout]


class AgentState(ABC):

    def __init__(self, my_agent, agent_indices):
        self._index = my_agent
        self._agent_indices = agent_indices
        self._sentences_said = []
        self._day = 1

    @abstractmethod
    def talk(self, task_manager):
        """
        Given the task manager that holds all the tasks at hand choose what to say next.
        :param task_manager:
        :return:
        """
        pass

    @abstractmethod
    def get_type(self):
        pass

    @abstractmethod
    def get_task_mask(self):
        """
        Get masking of tasks relevant to current state.
        :return:
        """

    def next_day(self):
        self._day += 1

    def check_sentence_said_before(self, sentence):
        """
        We don't want to replicate ourselves if we talk randomly.
        :param sentence
        :return:
        """
        for said_sentence in self._sentences_said:
            if compare_sentences(said_sentence, sentence):
                return True

        return False

    def ask_random_question(self):
        """
        Ask a random question toward a random agent target.
        :return:
        """
        random_subject = random.choice(self._agent_indices)
        random_target = random.choice([x for x in self._agent_indices if x != random_subject])
        question_pool = BASE_QUESTIONS.copy()
        params = {}

        # If there is any useful sentence we can ask whether the agents agrees or disagrees.
        useful_sentences = SentencesContainer.instance.has_useful_sentence_on_day(self._day, random_subject)
        if len(useful_sentences) != 0:
            question_pool += [do_you_agree_with, do_you_disagree_with]
            params["talk_number"] = random.choice(useful_sentences)

        params["subject"] = random_subject
        params["target"] = random_target
        params["role"] = random.choice(list(GameRoles))

        return random.choice(question_pool)(**params)

    def ask_unique_random_question(self):
        """
        We don't want to accidently repeat ourselves, this function makes sure we ask
        a question that wasn't said before.
        :return:
        """
        question = self.ask_random_question()
        while self.check_sentence_said_before(question):
            question = self.ask_random_question()

        return question






