
import threading
from typing import Callable

class Once:
    def __init__(self):
        self._lock = threading.Lock()
        self._done = False
        self._res = None

    def do(self, f: Callable[[], None]):
        if self._done:
            return self._res

        with self._lock:
            if self._done:
                return self._res
            try:
                self._res = f()
            except Exception:
                raise
            finally:
                self._done = True

    def done(self) -> bool:
        with self._lock:
            return self._done