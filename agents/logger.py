
class Logger(object):

    class __Logger:
        def __init__(self, file_name):
            self._file = open(file_name, 'w')

        def write(self, message):
            self._file.write(message + '\n')

        def close(self):
            self._file.close()

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