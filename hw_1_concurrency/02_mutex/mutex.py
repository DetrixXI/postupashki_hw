import threading
from collections import deque

FREE, HELD, CONTENDED = 0, 1, 2

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



class Mutex():
    def __init__(self):
        # используем для оченреди (фифо)
        self.queue = deque()
        # вроде как threadig.Lock и есть мютекс в питоне)
        self._thread_lock = threading.Lock()
        self._state = FREE

    def lock(self):
        with self._thread_lock:
            # реализуем 2 пути - быстрый и медленный
            # быстрый
            if self._state == FREE:
                self._state = HELD
                return
            
            # медленный
            # если уже был кем то знаят, то теперь состояние будет оспариваемым (т.к. 2 
            # процесса на него уже претендуют)
            if self._state == HELD:
                self._state = CONTENDED

            # в любом случае нужно добавить ивент в очередь
            event = Event()
            self.queue.append(event)

        # дальше поток спит (специально после полной
        # отработки _тред_лок через контекстный менеджер, чтобы не блокировать никого)
        # .sleep() спит, пока этот ивент кто то не релизнет с помощью 
        # wake, вытащив этот ивент из очереди
        event.sleep()

        
    def try_lock(self):
        with self._thread_lock:
            if self._state == FREE:
                self._state = HELD
                return True
            return False

    def unlock(self):
        with self._thread_lock:
            if self._state == FREE:
                raise RuntimeError()

            if self.queue:
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
            else:
                self._state= FREE

