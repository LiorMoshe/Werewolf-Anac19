
class Logger(object):

    class __Logger:
        def __init__(self, file_name):
            self._file = open(file_name, 'w')
            self._index = None

        def write(self, message):
            temp = 1
            #self._file.write("Agent[" + str(self._index) + "]: " + message + '\n')

        def close(self):
            self._file.close()

        def set_agent_index(self, index):
            self._index = index

    instance = None

    def __init__(self, file_name):
        if not Logger.instance:
            Logger.instance = Logger.__Logger(file_name)

    @staticmethod
    def log_list(logged_list, prefix_tabs = 1):
        logged_string = ""
        for member in logged_list:
            logged_string += '\t' * prefix_tabs + str(member) + '\n'
        return logged_string