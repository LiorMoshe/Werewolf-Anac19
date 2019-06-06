from agents.logger import Logger
from agents.information_processing.message_parsing import TalkNumber

class SentencesContainer(object):
    """
    Contains a mapping of talk number to dissected sentences. Used for recalls in cases of agreement or
    disagreement.
    Each talk number will map to a sentence which was said in this talk number.
    """

    class __SentencesContainer(object):

        def __init__(self):
            self.talk_number_to_sentences = {}

        def clean(self):
            Logger.instance.write("Cleaned the Sentence container")
            self.talk_number_to_sentences = {}
            Logger.instance.write("Len: " + str(len(self.talk_number_to_sentences)))

        def add_sentence(self, dissected_sentence):
            key_val = str(dissected_sentence.talk_number)
            Logger.instance.write(
                "Adding sentence of TalkNumber: " + str(key_val) + " to the sentence container " + str(len(self.talk_number_to_sentences)))
            if key_val not in self.talk_number_to_sentences.keys():
                self.talk_number_to_sentences[key_val] = dissected_sentence
            else:
                raise Exception("Two sentences shouldn't be saved for the same talk number: " + key_val +
                                "Message " + str(dissected_sentence.message) + " can't be saved because the message " +
                                str(self.talk_number_to_sentences[key_val].message) + "  is already saved.")

        def get_sentence(self, talk_number):
            return self.talk_number_to_sentences[str(talk_number)]

        def has_useful_sentence_on_day(self, day):
            """
            Checks whether a useful sentence was said on a given day,  useful
            when we want to check agreement or disagreement.
            A useful sentence is each sentence that is neither "skip" or "over"
            :param day:
            :return: List of all talk numbers of useful sentences said in the given day.
            """
            talk_numbers_on_day = []
            for talk_number, sentence in self.talk_number_to_sentences.items():
                if TalkNumber.is_on_day(talk_number, day):
                    talk_numbers_on_day.append(talk_number)

            return talk_numbers_on_day


    instance = None

    def __init__(self):
        if not SentencesContainer.instance:
            SentencesContainer.instance = SentencesContainer.__SentencesContainer()
