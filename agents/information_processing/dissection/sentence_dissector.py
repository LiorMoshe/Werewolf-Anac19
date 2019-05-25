from collections import namedtuple
from agents.information_processing.dissection.player_representation import Enemy, Cooperator
from agents.information_processing.message_parsing import *
from agents.game_roles import GameRoles


class DissectedSentence(object):
    """
    The result of a sentence dissection, can contain whether there is an enemy
    or cooperator created from the sentence, whether there is an admitted role
    in the sentence, subsentences of this sentence that were dissected (for example
    in a logic sentence which binds together several sentences) etc.
    """

    def __init__(self, message, talk_number, day):
        self.message = message
        self.talk_number = talk_number
        self.day = day
        self.cooperator = None
        self.enemy = None
        self.admitted_role = None
        self.directed_to_me = False
        self.dissected_subsentences = []

    def is_hostile(self):
        return self.enemy is not None and self.cooperator is None

    def has_subsentences(self):
        return len(self.dissected_subsentences) != 0


    def update_enemy(self, enemy):
        if self.enemy is None:
            self.enemy = enemy
        else:
            self.enemy.merge_enemies(enemy)

    def update_cooperator(self, cooperator):
        if self.cooperator is None:
            self.cooperator = cooperator
        else:
            self.cooperator.merge_cooperators(cooperator)

class SentenceDissector(object):
    """
    This is a singleton that will be used throughout the code to dissect meaning
    of sentences that are said by agents throughout the game, the state of this class is
    a map that will contain processed sentences (meaning they were already dissected)
    which will allow us to recall meaning of past sentences.
    """

    class __SentenceDissector(object):

        def __init__(self, sentences_container, my_agent):
            self._sentences_container = sentences_container
            self.my_agent = my_agent

        def dissect_sentence(self, message, talk_number, day,  scale=1, save_dissection=True):
            """
            Given a sentence return a DissectedSentence object which contains all relevant information
            extracted from the sentence.
            :param message:
            :param talk_number:
            :param day
            :param scale:
            :param save_dissection
            :return:
            """
            result = DissectedSentence(message, talk_number, day)
            if message.type == SentenceType.ESTIMATE or message.type == SentenceType.COMINGOUT:
                if message.target == message.subject:
                    result.admitted_role = {"role": message.role, "reason": message}
                elif GameRoles[message.role] == GameRoles.WEREWOLF or GameRoles[message.role] == GameRoles.POSSESSED:
                    result.enemy = self.create_enemy(message, hostility=1 / scale)

            elif message.type == SentenceType.VOTE:
                result.enemy = self.create_enemy(message, hostility=1.5 / scale)

            elif message.type == SentenceType.REQUEST:
                self.update_based_on_request(message, talk_number, result)
            elif message.type == SentenceType.INQUIRE:
                self.update_based_on_inquire(message, result)
            elif message.type == SentenceType.BECAUSE:
                self.update_because_sentence(message, talk_number, result)
            elif message.type == SentenceType.AGREE or message.type == SentenceType.DISAGREE:
                self.update_based_on_opinion(message, talk_number, result)
            elif message.type == SentenceType.XOR:
                self.update_based_on_xor(message, talk_number, result)
            elif message.type == SentenceType.OR:
                self.update_based_on_or(message, talk_number, result)
            elif message.type == SentenceType.NOT:
                self.update_based_on_not(message, talk_number, result)

            if save_dissection:
                self._sentences_container.add_sentence(result)

            return result

        def update_based_on_request(self, message, talk_number, dissected_sentence):
            """
            Update the perspective of this agent based on the given request.
            There are a lot of ways we can interpret a given request:
            1. If the request is from everyone (ANY) and it contains an estimate or knowledge sentence it's a direct
            blow against the target of this sentence, showing that this agent sees the target as it's enemy.
            2. In the case of requests of given actions that are actions that show cooperation like guarding and there
            are actions that show that this agent thinks of the target as an enemy like: divination, vote and attack (even
            though attack is only necessary for werewolves in the night phase).
            For each message give an increased hostility if it is hostile and the request is from everybody (ANY).
            :param message:
            :param talk_number
            :param dissected_sentence Result of dissection that will be filled.
            :return:
            """
            content = message.content

            if message.target != "ANY":
                # If there is a request towards someone we will see it as a sign of cooperation.
                dissected_sentence.update_cooperator(self.create_cooperator(message, fondness=2))

            if message.target == self.my_agent:
                dissected_sentence.directed_to_me = True

            if content.type == SentenceType.ESTIMATE or content.type == SentenceType.COMINGOUT:
                if GameRoles[content.role] == GameRoles.WEREWOLF or GameRoles[content.role] == GameRoles.POSSESSED:
                    hostility = 2 if message.target == "ANY" else 1
                    dissected_sentence.update_enemy(self.create_enemy(content, hostility=hostility))
                else:
                    fondness = 3 if message.target == "ANY" else 1
                    dissected_sentence.update_cooperator(self.create_cooperator(content, fondness=fondness))
            elif content.type == SentenceType.AGREE or content.type == SentenceType.DISAGREE:
                scale = 4 if message.target == "ANY" else 2
                self.update_based_on_opinion(content, talk_number, dissected_sentence, scale=scale)
            elif content.type == SentenceType.VOTE:
                hostility = 4 if message.target == "ANY" else 1.5
                dissected_sentence.update_enemy(self.create_enemy(content, hostility=hostility))
            elif content.type == SentenceType.DIVINE:
                hostility = 0.5 if message.target == "ANY" else 0.25
                dissected_sentence.update_enemy(self.create_enemy(content, hostility=hostility))
            elif content.type == SentenceType.GUARD:
                fondness = 3 if message.target == "ANY" else 1
                dissected_sentence.update_cooperator(self.create_cooperator(message, fondness))
            elif content.type == SentenceType.XOR:
                self.update_based_on_xor(message, talk_number, dissected_sentence)
            elif content.type == SentenceType.OR:
                self.update_based_on_or(message, talk_number, dissected_sentence)
            elif content.type == SentenceType.NOT:
                self.update_based_on_not(message, talk_number, dissected_sentence)
            elif content.type == SentenceType.ATTACK or content.type == SentenceType.IDENTIFIED:
                # TODO - Unsure if it's needed only used between werewolves, it's obvious they are cooperators.
                pass

        def update_based_on_xor(self, message, talk_number, dissected_sentence, reason=None):
            """
            Currently a xor message will be processed as two separate messages with lower scale for fondness or
            hostility of these messages because only one of them is true.
            TODO- We would maybe like to check resolvement of xor messages.
            :param message:
            :param talk_number
            :param dissected_sentence
            :param reason
            :return:
            """
            return self.update_based_on_or(message, talk_number, dissected_sentence, reason)

        def update_based_on_or(self, message, talk_number, dissected_sentence, reason=None):
            """
            Update based on given or message, current naive implementation updates based on each sentence with lower scale
            of fondness or hostility.
            TODO - Look at the most likely sentence based on my agent's perspective and scale the hostility or fondness
            based on the probabilities that my agent gives to one of these events happening based on his perspective.
            :param message:
            :param talk_number
            :param dissected_sentence
            :param reason
            :return:
            """
            scale = len(message.sentences)
            # result = None
            for sentence in message.sentences:
                sentence._replace(reason=reason)

                dissected_sentence.dissected_subsentences.append(self.dissect_sentence(sentence,
                                                                                       talk_number,
                                                                                       day=dissected_sentence.day,
                                                                                       scale=scale,
                                                                                       save_dissection=False))

        def reprocess_sentence(self, sentence, dissected_sentence, in_hostility, in_fondness):
            """
            Reprocess sentences that were already processed.
            :param sentence:
            :param dissected_sentence
            :param in_hostility: Method that will be used to update hostility depends on whether our opinion shows
            agreement or disagreement.
            :param in_fondness: Method that will be used to update fondness depends on whether our opinion shows
            agreement or disagreement.

            :return:
            """
            if sentence.is_hostile():
                in_hostility(dissected_sentence, sentence,  sentence.enemy.get_hostility(dissected_sentence.day))
            else:
                in_fondness(dissected_sentence, sentence, sentence.cooperator.get_fondness(dissected_sentence.day))

            if sentence.has_subsentences():
                for subsentence in sentence.dissected_subsentences:
                    self.reprocess_sentence(subsentence, dissected_sentence, in_hostility, in_fondness)

        def update_based_on_opinion(self, message, talk_number, dissected_sentence, scale=2):
            """
            Update the hostility or fondness of an agent based on a given opinion.
            :param message:
            :param talk_number
            :param dissected_sentence
            :param scale: Controls the amount of hostility or fondness, if an agent requests from everybody to agree
            with the statement of the other agent it means that he supports him much highly then a single agreement.
            :return:
            """
            in_hostility = in_fondness = None
            if message.type == SentenceType.AGREE:
                dissected_sentence.update_cooperator(self.create_cooperator(message.referencedSentence, fondness=scale))
                in_hostility = lambda main_sentence, sub_sentence, amount: main_sentence.update_enemy(
                    self.create_enemy(sub_sentence, hostility=amount))
                in_fondness = lambda main_sentence, sub_sentence, amount: main_sentence.update_cooperator(
                    self.create_cooperator(sub_sentence, fondness=amount))

            elif message.type == SentenceType.DISAGREE:
                dissected_sentence.update_enemy(self.create_enemy(message.referencedSentence, hostility=scale))
                in_hostility = lambda main_sentence, sub_sentence, amount: main_sentence.update_cooperator(
                    self.create_cooperator(sub_sentence, fondness=amount))
                in_fondness = lambda main_sentence, sub_sentence, amount: main_sentence.update_enemy(
                    self.create_enemy(sub_sentence, hostility=amount))

            processed_sentence = self._sentences_container.get_sentence(talk_number)
            self.reprocess_sentence(processed_sentence, dissected_sentence, in_hostility, in_fondness)

        def update_because_sentence(self, message, talk_number, dissected_sentence, scale=1):
            """
            Given a because sentence update the cooperators and enemies of this agent.
            Examples of because sentences that shows non cooperation:
            1. Because that x happened I will vote for agent 1.

            Examples for because sentences that show cooperation/
            1. Because that x happened I request anyone to guard agent 1 because he is valuable to the team.
            :param message:
            :param talk_number
            :param dissected_sentence
            :param scale
            :return:
            """
            cause, effect = message.sentences
            effect._replace(reason=cause)

            if effect.type == SentenceType.VOTE:
                dissected_sentence.update_enemy(self.create_enemy(effect, hostility=2 / scale))
            elif effect.type == SentenceType.DIVINE:
                dissected_sentence.update_cooperator(self.create_enemy(effect, hostility=1 / scale))
            elif effect.type == SentenceType.GUARD:
                dissected_sentence.update_cooperator(self.create_cooperator(effect, fondness=1 / scale))
            elif effect.type == SentenceType.AGREE or effect.type == SentenceType.DISAGREE:
                self.update_based_on_opinion(effect, talk_number, dissected_sentence, scale=3)
            elif effect.type == SentenceType.ESTIMATE or effect.type == SentenceType.COMINGOUT:
                if GameRoles[effect.role] == GameRoles.WEREWOLF or GameRoles[effect.role] == GameRoles.POSSESSED:
                    dissected_sentence.update_enemy(self.create_enemy(effect, hostility=4 / scale))
                else:
                    # If we estimate someone to not be in the werewolf team there is some fondness to it.
                    dissected_sentence.update_cooperator(self.create_cooperator(effect, fondness=1 / scale))
            elif effect.type == SentenceType.REQUEST:
                self.update_based_on_request(effect, talk_number, dissected_sentence)
            elif effect.type == SentenceType.INQUIRE:
                self.update_based_on_inquire(effect, dissected_sentence)
            elif effect.type == SentenceType.XOR:
                self.update_based_on_xor(message, talk_number, dissected_sentence, cause)
            elif effect.type == SentenceType.OR:
                self.update_based_on_or(effect, talk_number, dissected_sentence, cause)
            elif effect.type == SentenceType.AND:
                self.update_based_on_and(effect, talk_number, dissected_sentence, cause)
            elif effect.type == SentenceType.NOT:
                self.update_based_on_not(effect, talk_number, dissected_sentence)


        def update_based_on_and(self, message, talk_number, dissected_sentence, reason=None):
            # Process all sentences.
            for sentence in message.sentences:
                sentence._replace(reason=reason)
                dissected_sentence.dissected_subsentences.append(self.dissect_sentence(sentence, talk_number,
                                                                                       day= dissected_sentence.day,
                                                                                       save_dissection=False))

        def update_based_on_inquire(self, message, dissected_sentence):
            """
            Update the cooperators and enemies of this agent based on inquires that he sent throughout the game.
            TODO- Does asking questions mean anything about the relationship between two agents?
            :param message:
            :param talk_number
            :param dissected_sentence
            :return:
            """
            # Save inquires that are directed to our agent. Maybe we will answer.
            if message.target == self.my_agent:
                dissected_sentence.directed_to_me = True

        def update_based_on_not(self, message, talk_number, dissected_sentence):
            """
            Update based on negation sentence. Go over all the negated sentences and update the perspective using a
            negative scale. That way the sentence will get the exact opposite effect, if the original sentence shows
            hostility negating it will result as a sign of fondness and same vv.
            :param message:
            :param talk_number
            :param dissected_sentence
            :return:
            """
            for sentence in message.sentences:
                dissected_sentence.dissected_subsentences.append(self.dissect_sentence(sentence, talk_number,
                                                                                       day= dissected_sentence.day,
                                                                                       scale=-1,
                                                                                       save_dissection=False))

        def create_cooperator(self, message, fondness=1):
            """
            Given a sentence that shows some level of fondness create a Cooperator.
            We will also save the processed sentence in our sentence container before
            creating the cooperator.
            :param message:
            :param fondness:
            :return:
            """
            if fondness < 0:
               return self.create_enemy(message, hostility=-fondness)

            return Cooperator(message.target, history={}).update_fondness(fondness, message)
        
        def create_enemy(self, message, hostility=1):
            if hostility < 0:
                return self.create_cooperator(message, fondness=-hostility)

            return Enemy(message.target, history={}).update_hostility(hostility, message)
            
    instance = None

    def __init__(self, sentences_container, my_agent):
        if not SentenceDissector.instance:
            SentenceDissector.instance = SentenceDissector.__SentenceDissector(sentences_container, my_agent)
