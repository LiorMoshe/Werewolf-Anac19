

class SentencesContainer(object):
    """
    Contains a mapping of talk number to processed sentences. Used for recalls in cases of agreement or
    disagreement.
    """

    def __init__(self):
        self.talk_number_to_sentences = {}

    def add_sentence(self, talk_number, sentence):
        if talk_number not in self.talk_number_to_sentences.keys():
            self.talk_number_to_sentences[talk_number] = [sentence]
        else:
            self.talk_number_to_sentences[talk_number].append(sentence)

    def get_sentence(self, talk_number):
        return self.talk_number_to_sentences[talk_number]
