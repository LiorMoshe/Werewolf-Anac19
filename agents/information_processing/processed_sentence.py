

class ProcessedSentence(object):
    """
    This class represents a sentence that was already processed, we will save the sentence and the processing
    results, whether the sentence indicated fondness or hostility toward a given target.
    Main usage is to infer agents perspective when they recall specific moments in the game. For example:
    Agent 1 agrees with talk number 35, after looking at the processed sentence of talk number 35 we can see
    that this sentence shows hostility towards agent 2. Therefore agent 1 is also hostile towards agent 2.
    """

    def __init__(self, sentence, amount, is_hostile):
        self.sentence = sentence
        self.amount = amount
        self.is_hostile = is_hostile
        self.target = sentence.target

    @staticmethod
    def empty_sentence(message):
        """
        Generate an empty processed sentence for sentences that don't show fondness or hostility, a basic
        examples is in the case where an agent admits to a specific role
        :param message:
        :return:
        """
        return ProcessedSentence(message, 0, False)
