from enum import Enum
from collections import namedtuple

TaskTuple = namedtuple('TaskTuple', 'name includes_me')

class TaskType(Enum):
    """
    Holds all type of tasks that we will create.
    """
    SAME_ADMITTED_ROLE = TaskTuple("SAME_ADMITTED_ROLE", False),
    SAME_ADMITTED_ROLE_WITH_ME = TaskTuple("SAME_ADMITTED_ROLE_WITH_ME", True)
    REQUEST_VOTE_TYPE = TaskTuple("REQUEST_VOTE_TYPE", True)
    SEER_TASK = TaskTuple("SEER_TASK", False)

    def __str__(self):
        return self.name