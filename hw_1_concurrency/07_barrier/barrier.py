import threading
from typing import Callable


class Barrier:
    # вместо метода New, т.к. тут мы и создаем новый барьер по факту
    def __init__(self, n: int):
        self._need = n            
        self._arrived = 0          
        self._round = 0            
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)

    def wait(self) -> int:
        with self._lock:
            # запоминаем раунд
            round = self._round
            self._arrived += 1

            if self._arrived == self._need:
                self._arrived = 0
                self._cond.notify_all()

                self._round += 1
                return round

            # ждем смены раунда (а это происходит, когда набирается нужное кол_во участников)
            while self._round == round:
                self._cond.wait()

            return  round
