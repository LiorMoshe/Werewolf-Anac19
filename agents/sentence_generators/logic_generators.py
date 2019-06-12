from aiwolfpy.contentbuilder import *
from agents.game_roles import GameRoles

AND = "AND"
XOR = "XOR"
OR = "OR"
NOT = "NOT"
BECAUSE = "BECAUSE"

def wrap(sentence):
    return "(" + sentence + ")"

def and_sentence(*sentences):
    return base_logic_operator(AND, *sentences)

def base_logic_operator(operator, *sentences):
    total_sentences = [operator] + [sentence for sentence in sentences]
    return " ".join(total_sentences)

def xor_sentence(first_sentence, second_sentence):
    return " ".join([XOR, first_sentence, second_sentence])

def or_sentence(*sentences):
    return base_logic_operator(OR, *sentences)

def because_sentence(cause, effect):
    return " ".join([BECAUSE, cause, effect])

def estimate_bad_guy(target):
    return xor_sentence(wrap(estimate(target, str(GameRoles.WEREWOLF))),
                        wrap(estimate(target, str(GameRoles.POSSESSED))))

def estimate_bad_guys(*targets):
    """
    Given a list of targets estimate that at least one of them is a bad guy.
    :param targets:
    :return:
    """
    if len(targets)  == 1:
        return estimate_bad_guy(targets[0])

    else:
        sentences = []
        for target in targets:
            sentences.append(wrap(estimate_bad_guy(target)))

        return or_sentence(*sentences)
