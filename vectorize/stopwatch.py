import datetime


class Stopwatch:
    _start = None

    def start(self):
        self._start = datetime.datetime.now()

    def duration(self):
        return (datetime.datetime.now() - self._start).total_seconds()

    def reset(self):
        d = self.duration()
        self.start()
        return d