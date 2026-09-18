import threading
from collections import deque


class Event():
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


class Semaphore:
    def __init__(self, n: int = 5):
        if n < 0:
            raise ValueError("кол-во мест натуральное число")
        self._permits = n
        self._lock = threading.Lock()
        self._queue = deque()

    def acquire(self):
        # попробовать занять место. Если не вышло -
        # встать в очередь и ждать 

        # по аналогии с мютексом (который вроде как бинарный семафор)

        # такую конструкцию можно оформить через контекстный менеджер,
        # просто хотел показать, как она выглядит изнутрии
        self._lock.acquire(blocking=True)
        try:
            # здесь быстрый путь, если есть место
            if self._permits > 0:
                self._permits -= 1
                return
            # медленный путь, если мест нет, встаем в очередь
            waiter = Event()
            self._queue.append(waiter)
        finally:
            self._lock.release()

        # ждём, пока кто то нас не разлочит
        waiter.sleep()

    def try_acquire(self) -> bool:
        # попробовать занять место, если счетчик позволяет,
        # сообщить о том, получилось/нет
        with self._lock:
            if self._permits > 0:
                self._permits -= 1
                return True
            return False

    def release(self):
        # освободить место
        with self._lock:
            # если в очереди кто-то есть
            if self._queue:
                # здесь нельзя менять счетчик _permit т.к.
                # поток, ушедший в очередь находится на строчке
                # waiter.sleep() 50, т.е. этот поток сам не уменьшал self._permit 
                # и мы можем просто запустиь его вручную
                self._queue.popleft().wake()
            # и если никто не ждет (т.е. работали только мы)
            else:
                self._permits += 1



    def available(self) -> int:
        # сколько места осталось 

        # тоже делаем атомаорно, а то в процессе спрашивания
        # может и поменяться количество 
        with self._lock:
            return self._permits