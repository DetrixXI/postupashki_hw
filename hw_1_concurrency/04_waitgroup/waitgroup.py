import threading

class waitgroup():
    def __init__(self, n: int):
        if n < 0:
            raise ValueError('кол-во задач отрицательное число')

        self._num_of_tasks = n
        self._waiters = list()
        self._lock = threading.Lock()    

    def add(self, n: int):
        with self._lock:
            if n < 0:
                raise ValueError('некорректная добавка')
            self._num_of_tasks += n

    def done(self):
        with self._lock:
            self._num_of_tasks -= 1
            if self._num_of_tasks < 0:
                raise ValueError('done был выполнен больше, чем кол-во задач в wg')
            if self._num_of_tasks == 0:
                while self._waiters:
                    self._waiters.pop().release()


    def wait(self):
        with self._lock:
            if self._num_of_tasks == 0:
                return
            event = threading.Lock()
            self._waiters.append(event)
            event.acquire()

        event.acquire()

        ...