from agents.strategies.agent_strategy import TownsFolkStrategy
from agents.vote.townsfolk_vote_model import PossessedVoteModel

class PossessedStrategy(TownsFolkStrategy):
    def __init__(self, agent_indices, my_index, role_map, player_perspective):
        super().__init__(agent_indices, my_index, role_map, player_perspective)
        self._vote_model = PossessedVoteModel(agent_indices, my_index)