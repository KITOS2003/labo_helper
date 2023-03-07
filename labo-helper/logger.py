import time
import datetime

from colorama import Back, Fore, Style


class Logger:
    _initial_time = None
    _log = []

    def __init__(self, logfile=None):
        if Logger._initial_time is None:
            Logger._initial_time = time.time()
        self._log = []
        self._save_path = logfile
        if logfile is not None:
            self.file = open(self._save_path, "w")

    def get_time(self):
        time_str = str(datetime.timedelta(seconds=time.time() - Logger._initial_time))
        if time_str.find(".") != -1:
            time_str = time_str[: time_str.find(".")]
        return time_str

    def funcntion(self

    def error(self, head, msg):
        head = "{} ERR: {}".format(self.get_time(), head)
        print(Fore.BLACK + Back.RED, end="")
        print(head, end="")
        print(Style.RESET_ALL)
        print(Fore.RED, end="")
        print(msg)
        print(Style.RESET_ALL, end="")
        self._log.append(head + "\n" + msg + "\n")

    def warning(self, head, msg):
        head = "{} WARN: {}".format(self.get_time(), head)
        print(Fore.BLACK + Back.YELLOW, end="")
        print(head, end="")
        print(Style.RESET_ALL)
        print(Fore.YELLOW, end="")
        print(msg)
        print(Style.RESET_ALL, end="")
        self._log.append(head + "\n" + msg + "\n")

    def success(self, head, msg):
        head = "{}: {}".format(self.get_time(), head)
        print(Fore.BLACK + Back.GREEN, end="")
        print(head, end="")
        print(Style.RESET_ALL)
        print(Fore.GREEN, end="")
        print(msg)
        print(Style.RESET_ALL, end="")
        self._log.append(head + "\n" + msg + "\n")

    def message(self, msg):
        msg = "{} MSG: {}".format(self.get_time(), msg)
        print(msg)
        self._log.append(msg + "\n")

    def __del__(self):
        if self._save_path is not None:
            for msg in self._log:
                self.file.write(msg)
