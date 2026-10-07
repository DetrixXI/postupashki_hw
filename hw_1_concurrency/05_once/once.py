
import threading
from typing import Callable

class Once:
    def __init__(self):
        # за состояние "в процессе" отвечает лок 
        # (для получения снаружи нет интерфейса, но это вроде и не нужно, исходя из функционала Once)
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
            finally:
                self._done = True
            return self._res

    def done(self) -> bool:
        return self._done