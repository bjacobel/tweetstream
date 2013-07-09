import collections
import threading
import re


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

    # return the values for a key that all entries in the collection possess
    def inspect_value(self, key, subkey=None):
        with self.lock:
            values = []
            for event in self.events:
                if not subkey:
                    values.append(event[key])
                else:
                    values.append(event[key][subkey])
        return values

    # run on shutdown - or else python will wait for all of the events to expire
    def clear(self):
        with self.lock:
            self.events.clear()
