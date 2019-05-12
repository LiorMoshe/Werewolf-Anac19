
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
            print("CREATED LOGGER")
            Logger.instance = Logger.__Logger(file_name)
