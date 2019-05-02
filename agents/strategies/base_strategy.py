

class BaseStrategy(object):
    """
    Every basic strategy holds the probability of each agent having each one of the roles.
    This role map will help the agents make it's decisions.
    """

    def __init__(self):
        self._role_probs = {}
