import threading
from collections import deque
import time

FREE, HELD, CONTENDED = 0, 1, 2

class Custom_Event():
    # класс нужен для blocking-wait работы потоков 
    # (достигается а счет создания threading.Lock() каждый раз)
    def __init__(self):
        self.event_lock = threading.Lock()
        self.event_lock.acquire()

    def sleep(self):
        # т.е. тут поток заблокируется и "уснет", т.к
        # threading.Lock() уже занят и будет у нас blocking-wait
            self.event_lock.acquire()

    def wake(self):
        self.event_lock.release()
    


class Mutex():
    def __init__(self):
        # используем для оченреди (фифо)
        self.queue = deque()
        # вроде как threadig.Lock и есть мютекс в питоне)
        self._thread_lock = threading.Lock()
        self._state = FREE

    def _try_take(self):
        if self._state == FREE:
            self._state = HELD
            return True
        return False

    def lock(self):
        with self._thread_lock:
            if self._try_take():
                return
        
        for _ in range(10):
            time.sleep(0)
            with self._thread_lock:
                if self._try_take():
                    return

        event = Custom_Event()
        with self._thread_lock:
            if self._try_take():
                return
            self.queue.append(event)
            self._state = CONTENDED

        while True:
            event.sleep()
            with self._thread_lock():
                if self._try_take():
                    return
            self.queue.append(event)
            self._state = CONTENDED

        
    def try_lock(self):
        if not self._thread_lock.acquire(blocking=False):
            return False
        try:
            if self._state == FREE:
                self._state = HELD
                return True
            return False
        finally:
            self._thread_lock.release()
        

    def unlock(self):
        with self._thread_lock:
            if self._state == FREE:
                raise RuntimeError()
            if self._state == HELD:
                self._state == FREE
                return
            # вытаскиваем ивент от первого в очереди потока
            event = self.queue.popleft()
            # меняем состояние в зависимости от кол-ва ожидающих потоков
            # важно это сделать после popleft, т.к. мы вытащили из очереди задачу и,
            # возможно, она была последней (и тогда ставим held т.к. больше никто не
            # претендует на исполнение)
            self._state = CONTENDED if self.queue else HELD
            # тут у нашего объекта класса Event снимаем лок и тот, кто захолдился в .lock()
            # в конце поедет дальше
            event.wake()

