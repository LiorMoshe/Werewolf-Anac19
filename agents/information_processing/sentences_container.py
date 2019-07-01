

class SentencesContainer(object):
    """
    Contains a mapping of talk number to processed sentences. Used for recalls in cases of agreement or
    disagreement.
    """

    def __init__(self):
        self.talk_number_to_sentences = {}

    def add_sentence(self, talk_number, sentence):
        key_val = str(talk_number)
        if key_val not in self.talk_number_to_sentences.keys():
            self.talk_number_to_sentences[key_val] = [sentence]
        else:
            self.talk_number_to_sentences[key_val].append(sentence)

    def get_sentence(self, talk_number):
        return self.talk_number_to_sentences[str(talk_number)]
