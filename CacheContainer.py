import collections
import threading


class CacheContainer:
    def __init__(self, timeout=1):
        self.lock = threading.Lock()
        self.timeout = timeout
        self.events = collections.deque()

    def add(self, item):
        with self.lock:
            self.events.append(item)
            threading.Timer(self.timeout, self.expire).start()

    def len(self):
        with self.lock:
            return len(self.events)

    def expire(self):
        with self.lock:
            self.events.popleft()

    # return the values for a key that all entires in the collection possess
    def lookinside(self, key, key2=None):
        with self.lock:
            values = []
            for event in self.events:
                if not key2:
                    values.append(event[key])
                else:
                    values.append(event[key][key2])
        return values

    def clear(self):
        for event in self.events:
            event.expire()

