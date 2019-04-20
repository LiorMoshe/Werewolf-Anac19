from collections import namedtuple
from enum import Enum
import re


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
    BECAUSE = 15,
    AND = 16,
    XOR = 17,
    NOT = 18,
    OR = 19

#
# class LogicType(Enum):
#     AND = 1,
#     XOR = 2,
#     NOT = 3,
#     OR = 4,
#     BECAUSE = 5


KNOWLEDGE = [SentenceType.ESTIMATE, SentenceType.COMINGOUT]

ACTIONS = [SentenceType.ATTACK, SentenceType.GUARD, SentenceType.DIVINE, SentenceType.VOTE]

ACTION_RESULT = [SentenceType.ATTACKED, SentenceType.GUARDED, SentenceType.DIVINED, SentenceType.VOTED]


# Reason for a given sentence, holds two sentences.
# Reason = namedtuple('Reason', 'cause effect')

# Represents a logic statement made by a subject regarding the given sentences.
LogicStatement = namedtuple('LogicStatement', 'subject type sentences')

# Shows vote of an agent against specific agent, can hold reason if there is any.
Vote = namedtuple('Vote', 'votedAgainst type reason', defaults=(None, SentenceType.VOTE, None))

# An action done by the subject on the target.
Action = namedtuple('Action', 'subject target type day reason', defaults=(None, ) * 5)

# Result of an action of the subject on the target, if there is any new result it is held in species.
ActionResult = namedtuple('ActionResult', 'subject target species type day reason', defaults=(None,) * 6)

# Knowledge represents messages such as COMINGOUT, ESTIMATE where an agent thinks he knows something about other agents.
Knowledge = namedtuple('Knowledge', 'subject target role type reason', defaults=(None, 5))

KNOWLEDGE_TYPES = ['ESTIMATE', 'COMINGOUT']

AVAILABLE_ACTIONS = ['DIVINATION', 'GUARD', 'VOTE', 'ATTACK']

AVAILABLE_ACTION_RESULTS = ['DIVINED', 'IDENTIFIED', 'GUARDED', 'VOTED', 'ATTACKED']

LOGIC_OPERATORS = ['AND', 'XOR', 'NOT', 'OR', 'BECAUSE']


class RequestType(Enum):
    AGREEMENT = 1,
    ACTION = 2,
    ACTION_RESULT = 3


Request = namedtuple('Request', 'subject target content type')

Inquire = namedtuple('Inquire', 'subject target type')

# An opinion is used when an agent says whether he agrees or disagress with a given sentence
# (represented as talk number).
Opinion = namedtuple('Opinion', 'subject talk_number accept type')

def seperate_sentences(total_sentence):
    """
    Given a string representing several sentences, split them to a list of sentences.
    :param total_sentence:
    :return:
    """
    # seperators_indices = [0] + [m.start() + 1 for m in re.finditer("\) \(", total_sentence)] + [len(total_sentence)]
    # sentences = []
    #
    # for index_num, index in enumerate(seperators_indices[0: len(seperators_indices) - 1]):
    #     sentences.append(total_sentence[index: seperators_indices[index_num + 1]])
    #
    # return sentences
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

def fixed_seperate_sentences(total_sentence):
    starting_idx = total_sentence.find('(')
    sentences = []
    counter = 1
    for i in range(total_sentence):
        if total_sentence[i] == ')':
            counter -= 1
        elif total_sentence[i] == '(':
            counter += 1

        if counter == 0:
            sentences.append(total_sentence[starting_idx: i + 1])
            starting_idx = i + 1
        return sentences



def parse_general_sentence(sentence, validation_func, expected_num_words, object_builder):
    """
    All parsing of sentences is pretty similar, we get a sentence perform some validations
    and then create an object that represents it,  this is a general function which will be used
    to parse all the sentences.
    :param sentence:
    :param validation_func:
    :param expected_num_words:
    :param object_builder:
    :return:
    """
    parts_of_sentence = sentence.split(' ')

    if len(parts_of_sentence) not in expected_num_words:
        print("ERROR: There is different number of words than expected: " + str(expected_num_words) + " for sentence " +
              sentence)

    if not validation_func(parts_of_sentence):
        print("ERROR: The sentence " + sentence + " didn't pass validation")

    return object_builder(parts_of_sentence)


def parse_sentence_with_logic(sentence, agent_index=None):
    """
    Parse a sentence that contains a logic operator, this is sometimes paired with a subject
    and sometimes without it
    :param sentence:
    :param agent_index
    :return:
    """
    first_sentences_idx = sentence.find('(')
    prefix = sentence[:first_sentences_idx]
    sentences_content = [s for s in seperate_sentences(sentence[first_sentences_idx:]) if len(s.replace(' ','')) != 0]

    prefix_parts = prefix.split(' ')
    if prefix_parts[0] in LOGIC_OPERATORS:
        subject = agent_index
        operator_type = SentenceType[prefix_parts[0]]
    else:
        subject = prefix_parts[0]
        operator_type = SentenceType[prefix_parts[1]]

    # Parse the other sentences for which the logic is applied to.
    # Sentences are nested, we unbox them by taking first and last parantheses
    processed_sentences = []
    for sentence_content in sentences_content:
        first_parantheses = sentence_content.find('(')
        last_parantheses = sentence_content.rfind(')')
        processed_sentences.append(process_sentence(sentence_content[first_parantheses + 1:
                            last_parantheses],
                                                    agent_index))

    return LogicStatement(subject, operator_type, processed_sentences)


def process_sentence(sentence, agent_index=None, day=None):
    """
    Given a sentence of a player decide it's type and parse it by creating a matching
    object (which is defined above using named tuples).
    :param sentence: Sentence that will be parsed.
    :param agent_index: Index of the agent that parsed this sentence.
    :return: Object representing this sentence.
    """
    print("PROCESSING SENTENCE: " + sentence)
    result = None
    if any(logic_operator in sentence for logic_operator in LOGIC_OPERATORS):
        result = parse_sentence_with_logic(sentence,  agent_index)
    elif "DAY" in sentence:
        result = parse_with_time_info(sentence, agent_index)
    elif "REQUEST" in sentence:
        result = parse_request(sentence, agent_index,
                      lambda subject, target, content: Request(subject, target,
                                                               process_sentence(content.replace(')', '')),
                                                               SentenceType.REQUEST))
    elif "INQUIRE" in sentence:
        result = parse_request(sentence, agent_index,
                               lambda subject, target, content: Inquire(subject, target,
                                                                        process_sentence(content.replace(')', '',)),
                                                                        SentenceType.INQUIRE))
    elif "ESTIMATE" in sentence:
        result = parse_knowledge_sentence(sentence, agent_index)
    elif "COMINGOUT" in sentence:
        result = parse_knowledge_sentence(sentence, agent_index)
    elif "AGREE" in sentence:
        pass
    elif any(action in sentence for action in AVAILABLE_ACTIONS):
        result = parse_action_sentence(sentence, agent_index, day)
    elif any(action_result in sentence for action_result in AVAILABLE_ACTION_RESULTS):
        result = parse_past_action_sentence(sentence, day)

    return result


def parse_request(sentence, agent_idx, object_builder):
    request, content = sentence.split('(', 1)
    request_parts = [part for part in request.replace('(', '').split(' ') if len(part) != 0]

    if len(request_parts) == 2:
        subject = agent_idx
        target = request_parts[1]
    else:
        subject = request_parts[0]
        target = request_parts[2]

    if not ("REQUEST" in request_parts or "INQUIRE" in request_parts):
        print("ERROR: Cant parse sentence " + sentence + " cause it's not a request")

    return object_builder(subject, target, content)
    # return Request(subject, target, process_sentence(content.replace(')', '')))


def parse_knowledge_sentence(sentence, agent_index):
    """
    Return a Knowledge object based on the given sentence.
    :param sentence:  Sentence that represents some knowledge of a given agent.
    :return: Knowledge object.
    """
    parts_of_sentence = sentence.split(' ')
    if not (len(parts_of_sentence) == 4 or len(parts_of_sentence) == 3):
        print("Invalid number of words in sentence: " + sentence)

    if len(parts_of_sentence) == 3:
        subject = agent_index
        type = SentenceType[parts_of_sentence[0]]
        target = parts_of_sentence[1]
        role = parts_of_sentence[2]
    else:
        subject = parts_of_sentence[0]
        type = SentenceType[parts_of_sentence[1]]
        target = parts_of_sentence[2]
        role = parts_of_sentence[3]

    return Knowledge(subject, target, role, type)
    # return parse_general_sentence(sentence, lambda parts: parts[1] in KNOWLEDGE_TYPES, [4],
    #                               lambda parts: Knowledge(parts[0], parts[2], parts[3], SentenceType[parts[1]]))


def parse_past_action_sentence(sentence, agent_index=None, day=None):
    """
    Parse sentence that shows the result of past actions.
    :param sentence: Sentence that will be parsed.
    :return: ActionResult object.
    """
    parts_of_sentence = sentence.split(' ')
    if not (len(parts_of_sentence) == 3 or len(parts_of_sentence) == 4):
        print("ERROR: Invalid number of words in sentence:  " + sentence)

    species = None
    if len(parts_of_sentence) == 3:
        if parts_of_sentence[0] not in AVAILABLE_ACTION_RESULTS:
            subject = parts_of_sentence[0]
            type = parts_of_sentence[1]
            target = parts_of_sentence[2]
        else:
            subject = agent_index
            type = parts_of_sentence[0]
            target = parts_of_sentence[1]
            species = parts_of_sentence[2]
    else:
        subject = parts_of_sentence[0]
        type = parts_of_sentence[1]
        target = parts_of_sentence[2]
        species = parts_of_sentence[3]
    return ActionResult(subject, target, species, type, day)




    # return parse_general_sentence(sentence, lambda parts: parts[1] in AVAILABLE_ACTION_RESULTS, [3, 4],
    #                               lambda parts: ActionResult(parts[1], parts[0], parts[2],
    #                                                          None if len(parts) == 3 else parts[3],
    #                                                          SentenceType[parts[1]]))
def parse_with_time_info(sentence, agent_index):
    """
    Parse sentence that is paired with time info - what day was it.
    :param sentence:
    :param agent_index:
    :return:
    """
    day, content = sentence.split('(', 1)
    day_num = day.split(' ')[1]
    return process_sentence(content.replace(')', ''), day_num)

def parse_action_sentence(sentence, agent_index, day=None):
    """
    Parse sentence that represents an action done by an agent.
    :param sentence: Sentence that will be parsed.
    :return: Action object.
    """
    parts_of_sentence = sentence.split(' ')
    if not (len(parts_of_sentence) == 2 or len(parts_of_sentence) == 3):
        print("ERROR: Invalid number of words in sentence:  " + sentence)

    print("PARTS: ", parts_of_sentence)
    if len(parts_of_sentence) == 2:
        subject = agent_index
        type = SentenceType[parts_of_sentence[0]]
        target = parts_of_sentence[1]
    else:
        subject = parts_of_sentence[0]
        type = SentenceType[parts_of_sentence[1]]
        target = parts_of_sentence[2]

    return Action(subject, target, type, day)
    # return parse_general_sentence(sentence, lambda parts: parts[1] in AVAILABLE_ACTIONS, [2, 3],
    #                               lambda parts, has_subject: Action(parts[1], parts[0], parts[2], SentenceType[parts[1]]))

if __name__=="__main__":
    test = "AND (DAY 1 (Agent[03] DIVINED Agent[04] HUMAN)) (DAY 2 (Agent[03] DIVINED Agent[02] HUMAN))"
    test2 = "BECAUSE (DAY 2 (Agent[10] DIVINED Agent[06] WEREWOLF)) (REQUEST ANY (VOTE Agent[06]))"
    test3 = "REQUEST ANY (VOTE Agent[06])"
    test4="BECAUSE (AND (COMINGOUT Agent[04] VILLAGER) (DAY 3 (Agent[10] DIVINED Agent[04] WEREWOLF))) (XOR (ESTIMATE Agent[10] WEREWOLF) (ESTIMATE Agent[10] POSSESSED))"
    res = process_sentence(test4, agent_index=2)
    print(res)