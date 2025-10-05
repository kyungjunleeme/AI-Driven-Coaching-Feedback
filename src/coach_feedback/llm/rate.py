from __future__ import annotations
import threading, time

class SimpleRateLimiter:
    def __init__(self, calls_per_sec: float):
        self.interval = 1.0 / max(calls_per_sec, 1e-6)
        self.lock = threading.Lock()
        self.last = 0.0

    def acquire(self):
        with self.lock:
            now = time.time()
            wait = self.interval - (now - self.last)
            if wait > 0:
                time.sleep(wait)
            self.last = time.time()
