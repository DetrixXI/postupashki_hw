import threading
import time


class helper():
    # в моей рализации spin-lock и TTAS отличается только lock, потому
    # в helper вынес try_lock и unlock
    def __init__(self):
        self._lock = False
        
        # т.к. в питоне нет атомик.бул - берем тред.лок, чтобы 
        # обспечить атомарность над _lock (не совсем понял, можно ли так делать,
        # учитывая ограничения из условия дз)
        self._thread_lock = threading.Lock()
 
    def try_lock(self):
        # пробуем обратиться к self.__lock, если получится (т.е. тут нет цикла, как выше, спрашиваем 1 раз)
        if self._thread_lock.acquire(blocking=False):
            try:
                if self._lock == True:
                    return False
                
                self._lock = True
                return True
            finally:
                self._thread_lock.release()

        # это если не удалось забрать себе threading.Lock()
        else:        
            return False

    def unlock(self):
        # здесь надо обязательно освободить self.__lock, потому ставим acquire блокирующим
        self._thread_lock.acquire(blocking=True)
        try:
            if not self._lock:
                raise RuntimeError()
            self._lock = False
        finally:
            self._thread_lock.release()



class Spinlock(helper):
    # умышленно не использую контекстные менеджеры
    def lock(self):
        while True:
            # тут поток будет крутиться, если threading.Lock() занят другим потоком
            # ждать он будет не более timeout, потом вернет false если Lock
            # еще знаят, иначе - True. Т.е. поток реально крутится
            # пока не появится возможность атомарно обратиться к __lock, потом попробует 
            # занять __lock
            if self._thread_lock.acquire(blocking=False):
                # освобождаем тред.лок и выходим из метода Lock только тогда, когда сумели взять
                # self.__lock
                try:
                    if not self._lock:
                        self._lock = True
                        return
                finally:
                    self._thread_lock.release()
            # чтобы не крутился слишком быстро, иначе лишняя нагрузка на проц
            time.sleep(0.01)

class TTAS(helper):
    def lock(self):
        while True:
            # т.е. тут "дешево" просто читаем self.__lock, если 
            # он тру - все хорошо, продолжаем крутиться
            while self._lock:
                time.sleep(0.01)
                pass
            # сюда попадаем только если self.__lock стал false, т.е. освободился
            # пробуем его захватить, если не вышло - опять возвращаемся в начало
            if self._thread_lock.acquire(blocking=False):
                try:
                    if not self._lock:
                        self._lock = True
                        return
                finally:
                    self._thread_lock.release()

                



    
        
               

    






