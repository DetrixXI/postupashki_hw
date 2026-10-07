import threading
import time
from collections import deque

FREE, HELD, CONTENDED = 0, 1, 2


class Custom_Event:
    def __init__(self, wait_start):
        self.event_lock = threading.Lock()
        self.event_lock.acquire()
        self.handed = False
        self.wait_start = wait_start

    def sleep(self):
        self.event_lock.acquire()

    def wake(self, handed=False):
        self.handed = handed
        self.event_lock.release()


class Mutex:
    def __init__(self):
        self._queue = deque()
        self._thread_lock = threading.Lock()
        self._state = FREE
        self._spin_count = 3

        self._starving = False
        self._starv_limit = 0.1

    def _try_take(self):
        if self._state != FREE:
            return False
        self._state = CONTENDED if self._queue else HELD
        return True

    def try_lock(self):
        if not self._thread_lock.acquire(blocking=False):
            return False
        try:
            return self._try_take()
        finally:
            self._thread_lock.release()

    def lock(self):
        with self._thread_lock:
            if self._try_take():
                return

        for _ in range(self._spin_count):
            time.sleep(0)
            with self._thread_lock:
                if self._try_take():
                    return
                if self._starving:
                    break

        wait_start = time.monotonic()
        while True:
            event = Custom_Event(wait_start)
            with self._thread_lock:
                if self._try_take():
                    return
                self._queue.append(event)
                self._state = CONTENDED
            event.sleep()

            with self._thread_lock:
                if event.handed:
                    if not self._queue:
                        self._starving = False
                        self._state = HELD
                    return

                if self._try_take():
                    return

    def unlock(self):
        with self._thread_lock:
            if self._state == FREE:
                raise RuntimeError()
            if self._state == HELD:
                self._state = FREE
                self._starving = False
                return

            if not self._starving:
                if time.monotonic() - self._queue[0].wait_start > self._starv_limit:
                    self._starving = True

            event = self._queue.popleft()
            if self._starving:
                self._state = CONTENDED if self._queue else HELD
                event.wake(handed=True)
            else:
                self._state = FREE
                event.wake()
