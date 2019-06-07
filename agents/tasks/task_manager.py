from heapq import heappush, heappop

class PriorityQueue(object):
    """
    Python's base heapq module doesn't support efficient update of priorities so we have
    to implement the priority queueu by ourselves :).
    Note that heapq works based on the minimum so if we wish to get maximal value we will use negatives.
    """

    def __init__(self):
        self.items = []
        self.dict = {}

    def push(self, key, value):
        self.dict[key] = value
        heappush(self.items, (value, key))

    def __len__(self):
        return len(self.dict)

    def __contains__(self, item):
        return item in self.dict

    def _clear(self):
        value, key = self.items[0]
        while key not in self.dict or self.dict[key] != value:
            heappop(self.items)
            if not self.items:
                break

            value, key = self.items[0]

    def pop(self):
        if len(self.dict) == 0:
            raise IndexError("No values in the priority queue left to pop.")
        self._clear()

        value, key = heappop(self.items)
        del self.dict[key]

        if len(self.dict) > 0:
            self._clear()
        return key, value

    def peek(self):
        if len(self.dict) == 0:
            raise IndexError("No values in the dictionary, can't peek.")

        self._clear()
        value, key = self.items[0]
        return key, value



class TaskManager(object):
    """
    The TaskManager holds all the available tasks in a priority queue based on their given importance.
    It also makes sure to update the importance of the task as days go by.
    """

    def __init__(self):
        self._tasks = PriorityQueue()

    def add_task(self, task):
        self._tasks.push(task, task.get_importance())

    def add_tasks(self, tasks):
        for task in tasks:
            self.add_task(task)

    def empty(self):
        return len(self._tasks) == 0

    def num_tasks(self):
        return len(self._tasks)

    def get_most_important_task(self):
        return self._tasks.pop()[0]

    def peek_most_important_task(self):
        return self._tasks.peek()[0]

    def _pop_all(self):
        tasks = []
        for _ in range(len(self._tasks)):
            tasks.append(self._tasks.pop()[0])
        return tasks

    def update_tasks_importance(self, day):
        """
        As days go by we wish to update the importance of tasks in our priority queue.
        Pop all tasks from the queue and push them back with new values.
        :param day:
        :return:
        """
        tasks = self._pop_all()

        for task in tasks:
            task.update_importance_based_on_day(day)
            self._tasks.push(task, task.get_importance())

    def update_tasks_based_on_state(self, state_mask):
        """
        Given a state mask that gives a scaling factor from each TaskType to it's importance
        we update our priority queue based on the new scale.
        :param state_mask:
        :return:
        """
        tasks = self._pop_all()

        for task in tasks:
            task.update_importance_based_on_state()
            self._tasks.push(task, task.get_importance() * state_mask[task.get_type()])

if __name__ == "__main__":
    # Test the priority queue
    queue = PriorityQueue()
    queue.push(10, 50)
    queue.push(11, 90)
    print(queue.peek())
    queue.push(11, 20)

    print(queue.peek())
    print(queue.pop())
    print(queue.pop())
