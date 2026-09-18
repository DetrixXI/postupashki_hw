import threading
import time
import unittest
from typing import Callable
from rwmutex import RWMutex

def finished(f: Callable[[], None]) -> threading.Event:
    """Аналог Go finished: запускает f в потоке, возвращает Event."""
    event = threading.Event()
    def wrapper():
        try:
            f()
        except Exception:
            pass
        event.set()
    threading.Thread(target=wrapper).start()
    return event


class TestRWMutex(unittest.TestCase):

    def test_writer_excludes_everyone(self):
        """Пока писатель держит Lock, читатель и второй писатель не проходят."""
        rw = RWMutex()
        rw.lock()

        reader = finished(lambda: (rw.rlock(), rw.runlock()))
        writer = finished(lambda: (rw.lock(), rw.unlock()))

        time.sleep(0.05)  # даём потокам попытаться зайти

        self.assertFalse(reader.is_set(),
                         "читатель прошёл, пока держит писатель")
        self.assertFalse(writer.is_set(),
                         "второй писатель прошёл, пока держит первый")

        rw.unlock()

        self.assertTrue(reader.wait(timeout=2), "читатель не проснулся")
        self.assertTrue(writer.wait(timeout=2), "писатель не проснулся")

    def test_readers_go_together(self):
        """8 читателей проходят одновременно — пик >= 2."""
        rw = RWMutex()
        inside = [0]
        peak = [0]
        inside_lock = threading.Lock()

        def reader_worker():
            rw.rlock()
            with inside_lock:
                inside[0] += 1
                peak[0] = max(peak[0], inside[0])
            time.sleep(0.03)
            with inside_lock:
                inside[0] -= 1
            rw.runlock()

        threads = [threading.Thread(target=reader_worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)
            if t.is_alive():
                self.fail("читатели зависли")

        self.assertGreaterEqual(
            peak[0], 2,
            f"читатели шли по одному (пик {peak[0]}) — смысл RWMutex теряется"
        )

    def test_writer_waits_for_readers(self):
        """Писатель ждёт, пока все читатели не отпустят замок."""
        rw = RWMutex()
        rw.rlock()
        rw.rlock()

        writer = finished(lambda: (rw.lock(), rw.unlock()))

        time.sleep(0.05)
        self.assertFalse(writer.is_set(),
                         "писатель прошёл при живых читателях")

        rw.runlock()
        time.sleep(0.05)
        self.assertFalse(writer.is_set(),
                         "писатель прошёл, пока остался один читатель")

        rw.runlock()
        self.assertTrue(writer.wait(timeout=2),
                        "писатель не проснулся после последнего RUnlock")

    def test_no_torn_state(self):
        """Писатель делает shared++ дважды; читатель никогда не видит нечётное."""
        rw = RWMutex()
        shared = [0]
        bad = [False]
        shared_lock = threading.Lock()

        def writer_worker():
            for _ in range(500):
                rw.lock()
                with shared_lock:
                    shared[0] += 1
                    shared[0] += 1
                rw.unlock()

        def reader_worker():
            for _ in range(500):
                rw.rlock()
                with shared_lock:
                    if shared[0] % 2 != 0:
                        bad[0] = True
                rw.runlock()

        threads = []
        for _ in range(4):
            t = threading.Thread(target=writer_worker)
            threads.append(t)
            t.start()
        for _ in range(8):
            t = threading.Thread(target=reader_worker)
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=30)
            if t.is_alive():
                self.fail("нагрузочный тест завис")

        self.assertFalse(bad[0],
                         "читатель увидел состояние в середине записи")
        self.assertEqual(shared[0], 4 * 500 * 2,
                         f"записи потерялись: {shared[0]}")

    def test_unlock_without_lock_panics(self):
        """Unlock без Lock должен выбросить RuntimeError."""
        rw = RWMutex()
        with self.assertRaises(RuntimeError):
            rw.unlock()

    def test_runlock_without_rlock_panics(self):
        """RUnlock без RLock должен выбросить RuntimeError."""
        rw = RWMutex()
        with self.assertRaises(RuntimeError):
            rw.runlock()


if __name__ == "__main__":
    unittest.main(verbosity=2)