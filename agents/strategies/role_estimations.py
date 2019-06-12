

class RoleEstimations(object):
    """
    Holds estimations of players role based on my players view.
    """

    class __RoleEstimations(object):

        def __init__(self, indices, my_index):
            self.reset(indices, my_index)

        def reset(self, indices, my_index):
            self._estimations = {idx: [] for idx in indices}
            self.index = my_index


        def add_estimations(self, idx, roles):
            for role in roles:
                self.add_estimation(idx, role)

        def add_estimation(self, idx, role):
            if role not in self._estimations[idx]:
                self._estimations[idx].append(role)

        def get_estimations(self, idx):
            try:
                return self._estimations[idx]
            except KeyError:
                raise KeyError("FUCK index:" + str(idx) + " im " + str(self.index))


        def get_my_index(self):
            return self.index

    instance = None

    def __init__(self, indices, my_index):
        if RoleEstimations.instance is None:
            RoleEstimations.instance = RoleEstimations.__RoleEstimations(indices, my_index)
