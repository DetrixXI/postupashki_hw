import threading

class Waitgroup():
    def __init__(self, n: int = 0):
        if n < 0:
            raise RuntimeError('кол-во задач отрицательное число')

        self._num_of_tasks = n
        self._waiters = list()
        self._lock = threading.Lock()    

    def add(self, n: int):
        # специально запретил отрицательные значения, т.к. пользователь ведь тоже может воспользоваться этим
        # и, возможно, повредить логику работы wg. А так каждый метод отвечает за свою область - add добавляет, 
        # done - уменьшает и будит (эти действия логически связаны),
        # могу перенести всю логику сюда в add, но это вроде не критично ?
        with self._lock:
            if n < 0:
                raise RuntimeError('некорректная добавка')
            self._num_of_tasks += n

    def done(self):
        with self._lock:
            if self._num_of_tasks <= 0:
                raise RuntimeError('done был выполнен больше раз, чем кол-во задач в wg')
            self._num_of_tasks -= 1
            if self._num_of_tasks == 0:
                while self._waiters:
                    self._waiters.pop().release()


    def wait(self):
        with self._lock:
            if self._num_of_tasks == 0:
                return
            event = threading.Lock()
            event.acquire()
            self._waiters.append(event)
            

        event.acquire()
            
