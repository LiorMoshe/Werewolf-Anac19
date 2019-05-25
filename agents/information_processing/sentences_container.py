

class SentencesContainer(object):
    """
    Contains a mapping of talk number to dissected sentences. Used for recalls in cases of agreement or
    disagreement.
    Each talk number will map to a sentence which was said in this talk number.
    """

    def __init__(self):
        self.talk_number_to_sentences = {}

    def add_sentence(self, dissected_sentence):
        key_val = str(dissected_sentence.talk_number)
        if key_val not in self.talk_number_to_sentences.keys():
            self.talk_number_to_sentences[key_val] = dissected_sentence
        else:
            raise Exception("Two sentences shouldn't be saved for the same talk number: " + key_val +
                            "Message " + str(dissected_sentence.message) + " can't be saved because the message " +
                            str(self.talk_number_to_sentences[key_val]) + "  is already saved.")

    def get_sentence(self, talk_number):
        return self.talk_number_to_sentences[str(talk_number)]
