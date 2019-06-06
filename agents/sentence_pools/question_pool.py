"""
This file will contain all functions that will build for
us questions.
This will be used in cases we wish to generate a random question or ask
a valid one.
"""
INQUIRE = "INQUIRE"
OPENING_PARENTHESIS = "("
CLOSING_PARENTHESIS = ")"

VOTED = "VOTED"
VOTE = "VOTE"
ESTIMATE = "ESTIMATE"
COMINGOUT = "COMINGOUT"

ANY = "ANY"
AGREE = "AGREE"
DISAGREE = "DISAGREE"


def agent_str(idx):
    return "Agent" + str(idx) if idx != ANY else ANY


def who_voted_for(**kwargs):
    """
    Ask the agent which agent he voted for.
    TODO- Why would I ask that, I actually know it (they mentioned it in the protocol on github)
    :return:
    """
    subject = kwargs["subject"]
    target = kwargs["target"]

    return " ".join([INQUIRE, agent_str(subject), OPENING_PARENTHESIS, VOTED, agent_str(target), CLOSING_PARENTHESIS])


def who_will_vote_for(**kwargs):
    """
    Asks the agent which one he will vote for.
    :param target:
    :return:
    """
    subject = kwargs["subject"]
    target = kwargs["target"]

    return " ".join([INQUIRE, agent_str(subject), OPENING_PARENTHESIS, VOTE, agent_str(target), CLOSING_PARENTHESIS])


def do_you_estimate(**kwargs):
    """
    Asks the subject agent whether he thinks the target has the given role.
    :param subject:
    :param target:
    :param role:
    :return:
    """
    subject = kwargs["subject"]
    target = kwargs["target"]
    role = kwargs["role"]

    return " ".join(
        [INQUIRE, agent_str(subject), OPENING_PARENTHESIS, ESTIMATE, agent_str(target), str(role), CLOSING_PARENTHESIS])

def do_you_comingout(**kwargs):
    """
    Same as do_you_estimate just for the coming out case.
    :param subject:
    :param target:
    :param role:
    :return:
    """
    subject = kwargs["subject"]
    target = kwargs["target"]
    role = kwargs["role"]

    return " ".join(
        [INQUIRE, agent_str(subject), OPENING_PARENTHESIS, COMINGOUT, agent_str(target), str(role), CLOSING_PARENTHESIS])


def do_you_agree_with(**kwargs):
    subject = kwargs["subject"]
    talk_number = kwargs["talk_number"]
    return " ".join([INQUIRE, agent_str(subject), OPENING_PARENTHESIS, AGREE, talk_number, CLOSING_PARENTHESIS])

def do_you_disagree_with(**kwargs):
    print(kwargs)
    subject = kwargs["subject"]
    talk_number = kwargs["talk_number"]

    return " ".join([INQUIRE, agent_str(subject), OPENING_PARENTHESIS, DISAGREE, talk_number, CLOSING_PARENTHESIS])


