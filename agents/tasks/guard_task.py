from agents.tasks.base_task import BaseTask
from agents.tasks.task_type import TaskType
from agents.sentence_generators.logic_generators import *
from operator import itemgetter

class GuardTask(BaseTask):
    """
    We will use this task if we want the medium that we trust to identify
    a role of agent that was executed or attacked in the game.
    """

    def __init__(self, importance, day, relevant_agents, my_index, guard_idx, target_idx):
        BaseTask.__init__(self, importance, day, relevant_agents, my_index)
        self._bodyguard = guard_idx
        self._target = target_idx

    def update_importance_based_on_day(self, day):
        pass

    def get_type(self):
        return TaskType.GUARD_TASK

    def handle_task(self, **kwargs):
        return request_sentence(self._bodyguard, wrap(guard(self._target)))

    @staticmethod
    def generate_guard_task(game_graph, my_index, guard_idx, num_agents, importance,
                            day):
        """
        Based on my index and the game graph find the cooperator which is most likely to get attacked
        and ask the guard to guard him.
        :param game_graph:
        :param my_index
        :param guard_idx
        :param num_agents Number of agents that are currently in the game.
        :param importance
        :param  day
        :return:
        """
        top_cooperators = game_graph.get_node(my_index).get_top_k_cooperators(k=int(num_agents / 2))
        idx_to_evaluation = {}

        for idx in top_cooperators:
            idx_to_evaluation[idx] = game_graph.get_node(idx).evaluate(reversed_context=True)

        at_risk_idx =  max(idx_to_evaluation.items(), key=itemgetter(1))[0]
        return GuardTask(importance, day, [at_risk_idx, guard_idx], my_index, guard_idx, at_risk_idx)
