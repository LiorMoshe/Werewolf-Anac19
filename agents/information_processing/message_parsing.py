from collections import namedtuple
from enum import Enum


class Species(Enum):
    HUMANS = 1,
    WEREWOLVES = 2

# Just because we hate magic numbers
DAY_STRING_LENGTH = len("Day")

def append_zero(num, required_digits=1):
    """
    Given a number append a zero to it if it has a single digit, used for the talk number's
    string format.
    :param num:
    :param required_digits
    :return:
    """
    return "0" * (required_digits - int(num / (10  ** required_digits))) + str(num)


class TalkNumber(object):

    def __init__(self, day, talk_turn, idx):
        self.day = day
        self.idx = idx
        self.talk_turn = talk_turn

    def __str__(self):
        return "Day" + append_zero(self.day) + " " + append_zero(self.talk_turn) + "[" + \
                   str(append_zero(self.idx, required_digits=2)) + "]"

    @staticmethod
    def is_on_day(talk_number, day):
        """
        Given string representation of a talk number check if it's on a given day.
        :param talk_number:
        :param day:
        :return:
        """
        return talk_number.split(' ', 1)[0][DAY_STRING_LENGTH:]

    def __eq__(self, other):
        return self.day == other.day and self.idx == other.idx and self.talk_turn == other.talk_turn

class SentenceType(Enum):
    ESTIMATE = 1,
    COMINGOUT = 2,
    REQUEST = 3,
    INQUIRE = 4,
    AGREE = 5,
    DISAGREE = 6,
    ATTACK = 7,
    GUARD = 8,
    DIVINE = 9,
    VOTE = 10,
    ATTACKED = 11,
    GUARDED = 12,
    DIVINED = 13,
    VOTED = 14,
    IDENTIFIED = 15
    BECAUSE = 16,
    AND = 17,
    XOR = 18,
    NOT = 19,
    OR = 20


KNOWLEDGE = [SentenceType.ESTIMATE, SentenceType.COMINGOUT]

ACTIONS = [SentenceType.ATTACK, SentenceType.GUARD, SentenceType.DIVINE, SentenceType.VOTE]

ACTION_RESULT = [SentenceType.ATTACKED, SentenceType.GUARDED, SentenceType.DIVINED, SentenceType.VOTED]

# Reason for a given sentence, holds two sentences.
# Reason = namedtuple('Reason', 'cause effect')

# Represents a logic statement made by a subject regarding the given sentences.
LogicStatement = namedtuple('LogicStatement', 'subject type sentences reason day described_day')

# Shows vote of an agent against specific agent, can hold reason if there is any.
Vote = namedtuple('Vote', 'subject target type reason day described_day')

# An action done by the subject on the target.
Action = namedtuple('Action', 'subject target type reason day described_day')

# Result of an action of the subject on the target, if there is any new result it is held in species.
ActionResult = namedtuple('ActionResult', 'subject target species type reason day described_day')

# Knowledge represents messages such as COMINGOUT, ESTIMATE where an agent thinks he knows something about other agents.
Knowledge = namedtuple('Knowledge', 'subject target role type reason day described_day')

KNOWLEDGE_TYPES = ['ESTIMATE', 'COMINGOUT']

AVAILABLE_ACTIONS = ['DIVINATION', 'GUARD', 'VOTE', 'ATTACK']

AVAILABLE_ACTION_RESULTS = ['DIVINED', 'IDENTIFIED', 'GUARDED', 'VOTED', 'ATTACKED']

LOGIC_OPERATORS = ['AND', 'XOR', 'NOT', 'OR', 'BECAUSE']

Request = namedtuple('Request', 'subject target content type reason day described_day')

Inquire = namedtuple('Inquire', 'subject target content type reason day described_day')

# An opinion is used when an agent says whether he agrees or disagrees with a given sentence
# (represented as talk number).
Opinion = namedtuple('Opinion', 'subject talk_number type referencedSentence day described_day')


def extract_agent_idx(message):
    """
    Given message that states the agent index, for example: Agent[1]. Extract the index
    of this agent (in the case of the example it is 1).
    :param message:
    :return:
    """
    if "[" in message and "]" in message:
        return int(message[message.find("[") + 1:message.find("]")])
    return message


def separate_sentences(total_sentence):
    """
    Given a string representing several sentences, split them to a list of sentences.
    :param total_sentence:
    :return:
    """
    starting_idx = total_sentence.find('(')
    sentences = []
    counter = 0
    for i in range(len(total_sentence)):
        if total_sentence[i] == ')':
            counter -= 1
        elif total_sentence[i] == '(':
            counter += 1

        if counter == 0:
            sentences.append(total_sentence[starting_idx: i + 1])
            starting_idx = i + 1
    return sentences


class MessageParser(object):

    def __init__(self):
        self._talk_number_to_message = {}

    def parse_sentence_with_logic(self, sentence, agent_index, day, talk_number, described_day):
        """
        Parse a sentence that contains a logic operator, this is sometimes paired with a subject
        and sometimes without it
        :param sentence:
        :param agent_index
        :param day
        :param talk_number
        :param described_day
        :return:
        """
        first_sentences_idx = sentence.find('(')
        prefix = sentence[:first_sentences_idx]
        sentences_content = [s for s in separate_sentences(sentence[first_sentences_idx:]) if
                             len(s.replace(' ', '')) != 0]

        prefix_parts = prefix.split(' ')
        if prefix_parts[0] in LOGIC_OPERATORS:
            subject = agent_index
            operator_type = SentenceType[prefix_parts[0]]
        else:
            subject = extract_agent_idx(prefix_parts[0])
            operator_type = SentenceType[prefix_parts[1]]

        # Parse the other sentences for which the logic is applied to.
        # Sentences are nested, we unbox them by taking first and last parantheses
        processed_sentences = []
        for sentence_content in sentences_content:
            first_parantheses = sentence_content.find('(')
            last_parantheses = sentence_content.rfind(')')
            processed_sentences.append(self.process_sentence(sentence_content[first_parantheses + 1:
                                                                              last_parantheses],
                                                             agent_index, day, talk_number, described_day))

        return LogicStatement(subject=subject, type=operator_type, sentences=processed_sentences,
                              reason=None, day=day, described_day=described_day)

    def process_sentence(self, sentence, agent_index, day, talk_number, described_day=None):
        """
        Given a sentence of a player decide it's type and parse it by creating a matching
        object (which is defined above using named tuples).
        :param sentence: Sentence that will be parsed.
        :param agent_index: Index of the agent that said this sentence.
        :param day Day of the message, if it's stated.
        :param talk_number The talk number of this message, idx in the pandas dataframe.
        :param described_day Day stated in the message (for example, on Day 1 agent x said ...).
        :return: Object representing this sentence.
        """
        # print("PROCESSING SENTENCE: " + sentence)
        result = None
        if any(logic_operator in sentence for logic_operator in LOGIC_OPERATORS):
            result = self.parse_sentence_with_logic(sentence, agent_index, day, talk_number, described_day)
        elif "DAY" in sentence:
            result = self.parse_with_time_info(sentence, agent_index, day, talk_number)
        elif "REQUEST" in sentence:
            result = MessageParser.parse_request(sentence, agent_index,
                                                 lambda subject, target, content: Request(subject=subject,
                                                                                          target=target,
                                                                                          content=self.process_sentence(
                                                                                              content.replace(')', ''),
                                                                                              subject, day,
                                                                                              talk_number,
                                                                                              described_day),
                                                                                          type=SentenceType.REQUEST,
                                                                                          reason=None,
                                                                                          day=day,
                                                                                          described_day=described_day))
        elif "INQUIRE" in sentence:
            result = MessageParser.parse_request(sentence, agent_index,
                                                 lambda subject, target, content: Inquire(subject=subject,
                                                                                          target=target,
                                                                                          content=self.process_sentence(
                                                                                              content.replace(')', ''),
                                                                                              subject, day,
                                                                                              talk_number,
                                                                                              described_day),
                                                                                          type=SentenceType.INQUIRE,
                                                                                          reason=None,
                                                                                          day=day,
                                                                                          described_day=described_day))
        elif "ESTIMATE" in sentence or "COMINGOUT" in sentence:
            result = MessageParser.parse_knowledge_sentence(sentence, agent_index, day, described_day)
        elif "AGREE" in sentence or "DISAGREE" in sentence:
            self.parse_opinion(sentence, agent_index, day, described_day)
        elif any(action in sentence for action in AVAILABLE_ACTIONS):
            result = MessageParser.parse_action_sentence(sentence, agent_index, day, described_day)
        elif any(action_result in sentence for action_result in AVAILABLE_ACTION_RESULTS):
            result = MessageParser.parse_past_action_sentence(sentence, agent_index, day, described_day)

        self._talk_number_to_message[str(talk_number)] = result
        return result

    def parse_opinion(self, sentence, agent_idx, day, described_day):
        """
        Parse a sentence where the agent states it's opinion regarding a specific sentence.
        Recall the sentence using our saved dictionary of messages and return an
        Opinion object.
        :param sentence:
        :param agent_idx:
        :param day:
        :param described_day:
        :return:
        """
        splitted_sentence = sentence.split(' ')

        if len(splitted_sentence) == 2:
            subject = agent_idx
            opinion_type = SentenceType[splitted_sentence[0]]
            talk_number = int(splitted_sentence[1])
        else:
            subject = extract_agent_idx(splitted_sentence[0])
            opinion_type = SentenceType[splitted_sentence[1]]
            talk_number = int(splitted_sentence[2])

        return Opinion(subject, talk_number, opinion_type, self._talk_number_to_message[talk_number], day,
                       described_day)

    @staticmethod
    def parse_request(sentence, agent_idx, object_builder):
        """
        Process a request sent from a player.
        In the case of a missing subject in the sentence representing the request (UNSPEC) we will take the subject
        to be the subject of the parent sentence if the request is nested inside a sentence. If the request is not nested
        the subject will be the speaker.
        :param sentence:
        :param agent_idx:
        :param object_builder:
        :return:
        """
        request, content = sentence.split('(', 1)
        request_parts = [part for part in request.replace('(', '').split(' ') if len(part) != 0]

        if len(request_parts) == 2:
            subject = agent_idx
            target = extract_agent_idx(request_parts[1])
        else:
            subject = extract_agent_idx(request_parts[0])
            target = extract_agent_idx(request_parts[2])

        if not ("REQUEST" in request_parts or "INQUIRE" in request_parts):
            print("ERROR: Cant parse sentence " + sentence + " cause it's not a request")

        return object_builder(subject, target, content)

    @staticmethod
    def parse_knowledge_sentence(sentence, agent_index, day, described_day):
        """
        Return a Knowledge object based on the given sentence.
        :param sentence:  Sentence that represents some knowledge of a given agent.
        :param agent_index
        :param day
        :param described_day
        :return: Knowledge object.
        """
        parts_of_sentence = sentence.split(' ')
        if not (len(parts_of_sentence) == 4 or len(parts_of_sentence) == 3):
            print("Invalid number of words in sentence: " + sentence)

        if len(parts_of_sentence) == 3:
            subject = agent_index
            knowledge_type = SentenceType[parts_of_sentence[0]]
            target = extract_agent_idx(parts_of_sentence[1])
            role = parts_of_sentence[2]
        else:
            subject = extract_agent_idx(parts_of_sentence[0])
            knowledge_type = SentenceType[parts_of_sentence[1]]
            target = extract_agent_idx(parts_of_sentence[2])
            role = parts_of_sentence[3]

        return Knowledge(subject=subject, target=target, role=role, type=knowledge_type,
                         reason=None, day=day, described_day=described_day)

    @staticmethod
    def parse_past_action_sentence(sentence, agent_index, day, described_day):
        """
        Parse sentence that shows the result of past actions.
        :param sentence: Sentence that will be parsed.
        :param agent_index
        :param day
        :param described_day
        :return: ActionResult object.
        """
        parts_of_sentence = sentence.split(' ')
        if not (len(parts_of_sentence) == 3 or len(parts_of_sentence) == 4):
            print("ERROR: Invalid number of words in sentence:  " + sentence)

        species = None
        if len(parts_of_sentence) == 3:
            if parts_of_sentence[0] not in AVAILABLE_ACTION_RESULTS:
                subject = extract_agent_idx(parts_of_sentence[0])
                action_type = parts_of_sentence[1]
                target = extract_agent_idx(parts_of_sentence[2])
            else:
                subject = agent_index
                action_type = parts_of_sentence[0]
                target = extract_agent_idx(parts_of_sentence[1])
                species = parts_of_sentence[2]
        else:
            subject = extract_agent_idx(parts_of_sentence[0])
            action_type = parts_of_sentence[1]
            target = extract_agent_idx(parts_of_sentence[2])
            species = parts_of_sentence[3]
        return ActionResult(subject=subject, target=target, species=species, type=action_type,
                            reason=None, day=day, described_day=described_day)

    def parse_with_time_info(self, sentence, agent_index, day, talk_number):
        """
        Parse sentence that is paired with time info - what day was it.
        :param sentence:
        :param agent_index:
        :param talk_number
        :return:
        """
        day_num, content = sentence.split('(', 1)
        described_day = int(day_num.split(' ')[1])
        return self.process_sentence(content.replace(')', ''), agent_index, day, talk_number,
                                     described_day=described_day)

    @staticmethod
    def parse_action_sentence(sentence, agent_index, day, described_day):
        """
        Parse sentence that represents an action done by an agent.
        :param sentence: Sentence that will be parsed.
        :param agent_index
        :param day
        :param described_day
        :return: Action object.
        """
        parts_of_sentence = sentence.split(' ')
        if not (len(parts_of_sentence) == 2 or len(parts_of_sentence) == 3):
            print("ERROR: Invalid number of words in sentence:  " + sentence)

        if len(parts_of_sentence) == 2:
            subject = agent_index
            action_result_type = SentenceType[parts_of_sentence[0]]
            target = extract_agent_idx(parts_of_sentence[1])
        else:
            subject = extract_agent_idx(parts_of_sentence[0])
            action_result_type = SentenceType[parts_of_sentence[1]]
            target = extract_agent_idx(parts_of_sentence[2])

        return Action(subject=subject,  target=target, type=action_result_type,
                      reason=None, day=day, described_day=described_day)


if __name__ == "__main__":
    test = "AND (DAY 1 (Agent[03] DIVINED Agent[04] HUMAN)) (DAY 2 (Agent[03] DIVINED Agent[02] HUMAN))"
    test2 = "BECAUSE (DAY 2 (Agent[10] DIVINED Agent[06] WEREWOLF)) (REQUEST ANY (VOTE Agent[06]))"
    test3 = "REQUEST ANY (VOTE Agent[06])"
    test4 = "BECAUSE (AND (COMINGOUT Agent[04] VILLAGER) (DAY 3 (Agent[10] DIVINED Agent[04] WEREWOLF))) (XOR (ESTIMATE Agent[10] WEREWOLF) (ESTIMATE Agent[10] POSSESSED))"
    test5 = "DAY 1 (Agent[11] DIVINED Agent[10] WEREWOLF)"
    parser = MessageParser()
    res = parser.process_sentence(test5, agent_index=2, day=3, talk_number=4)
    print(res)
