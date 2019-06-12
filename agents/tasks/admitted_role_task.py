from agents.tasks.base_task import BaseTask
from agents.sentence_generators.logic_generators import *
from agents.tasks.task_type import TaskType
from agents.strategies.role_estimations import RoleEstimations

DISCOUNT_FACTOR = 0.9

class AdmittedRoleTask(BaseTask):
    """
    This task represents the time where two (or more) agents admit to the same special role, meaning
    a role that can be held by just one agent, meaning at least one of them is lying.
    """

    def __init__(self, importance, day, relevant_agents, admitted_role, reference_sentences,
                 my_index):
        """
        :param admitted_role: Role admitted
        :param relevant_agents: Players admitted to these roles.
        :param reference_sentences: Sentences in which agents admitted to some role.
        :param  importance: Importance of this task
        :param day: Day in which it happened.
        :param my_index: index of my agent.
        """
        BaseTask.__init__(self, importance, day, relevant_agents, my_index)
        self._admitted_role = admitted_role
        self._referenced_sentences = reference_sentences

    def get_type(self):
        return TaskType.SAME_ADMITTED_ROLE_WITH_ME if self.is_included() else TaskType.SAME_ADMITTED_ROLE

    def update_importance_based_on_day(self, day):
        self._importance *= DISCOUNT_FACTOR * (day - self._day)

    def handle_task(self, **kwargs):
        """
        Build a response that explain the lie we just caught and accuse the on of the liars to be
        either a werewolf or possessed.
        :param kwargs:
        :return:
        """
        admitted_sentences = [wrap(sentence.original_message) for sentence in self._referenced_sentences]
        if self.is_included():

            admitted_sentences = [wrap(comingout(self.index, self._admitted_role))] + admitted_sentences

        for sentence in self._referenced_sentences:
            if sentence.subject != self.index:
                RoleEstimations.instance.add_estimations(sentence.subject, [GameRoles.POSSESSED, GameRoles.WEREWOLF])



        # Show all coming out sentences and accuse everyone beside me to be either werewolf or possessed.
        return because_sentence(
            wrap(and_sentence(*admitted_sentences)),
            wrap(estimate_bad_guys(*self.relevant_agents_beside_me()))
        )

