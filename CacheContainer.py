import collections
import threading


class CacheContainter:
    def __init__(self, timeout=1):
        self.lock = threading.Lock()
        self.timeout = timeout
        self.events = collections.deque()

    def add(self, item):
        with self.lock:
            self.events.append(item)
            threading.Timer(self.timeout, self.expire).start()

    def __len__(self):
        with self.lock:
            return len(self.events)

    def expire(self):
        with self.lock:
            self.events.popleft()

    def __str__(self):
        with self.lock:
            return str(self.events)
