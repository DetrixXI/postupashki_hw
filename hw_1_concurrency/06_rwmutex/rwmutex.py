import threading

WRITER = 1 << 31


class RWMutex:

    def __init__(self):
        self._state = 0
        self._lock = threading.Lock()
        self._cond = threading.Condition(self._lock)

    def rlock(self):
        with self._lock:                       
            # тут пока в старщем бите (писательском) != 1, мы будем 
            # засыпать и, при пробудеждении снова проверять, есть ли писатель
            while self._state & WRITER:
                self._cond.wait()
            # пришли сюда только если писателя нет - увеличиваем кол-во читателей
            self._state += 1

    def runlock(self):
        with self._lock:
            if not (self._state & ~WRITER):
                raise RuntimeError("Ранлок без активных читателей")
            self._state -= 1
            if not (self._state & ~WRITER):
                # будим всех, кто уснул на локе, чтобы они проверили, есть ли для них место
                # и могу ли они вообще войти
                self._cond.notify_all()

    def lock(self):
        with self._lock:
            while self._state & WRITER:
                self._cond.wait()

            # писательский бит
            self._state |= WRITER

            # ждём, пока уже читающие не дочитают
            while self._state & ~WRITER:
                self._cond.wait()

    def unlock(self):
        with self._lock:
            if not (self._state& WRITER):
                raise RuntimeError('Анлок без активного читателя')
            self._state &= ~WRITER
            self._cond.notify_all()
