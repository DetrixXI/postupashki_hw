import threading
import time
import unittest
from semaphore import Semaphore


def finished(f):
    """Запускает f в потоке, возвращает Event, который сработает после завершения."""
    event = threading.Event()
    def wrapper():
        f()
        event.set()
    threading.Thread(target=wrapper, daemon=True).start()
    return event


class TestSemaphore(unittest.TestCase):

    def test_acquire_release(self):
        s = Semaphore(2)

        self.assertEqual(s.available(), 2,
                         f"Available вернул {s.available()}, ожидалось 2")

        s.acquire()
        s.acquire()

        self.assertEqual(s.available(), 0,
                         f"Available вернул {s.available()}, ожидалось 0")

        s.release()
        s.release()

        self.assertEqual(s.available(), 2,
                         f"Available вернул {s.available()}, ожидалось 2")

    def test_blocks_when_empty(self):
        s = Semaphore(1)
        s.acquire()

        second = finished(lambda: (s.acquire(), s.release()))

        # Acquire не должен пройти за 50 мс
        self.assertFalse(second.wait(timeout=0.05),
                        "Acquire прошёл, хотя разрешений нет")

        s.release()

        # После release acquire должен завершиться за 2 секунды
        self.assertTrue(second.wait(timeout=2.0),
                       "Acquire не проснулся после Release")

    def test_never_more_than_limit(self):
        limit = 3
        s = Semaphore(limit)

        inside = 0
        peak = 0
        state_lock = threading.Lock()

        def worker():
            nonlocal inside, peak
            s.acquire()

            with state_lock:
                inside += 1
                if inside > peak:
                    peak = inside

            time.sleep(0.001)

            with state_lock:
                inside -= 1

            s.release()

        threads = [threading.Thread(target=worker) for _ in range(40)]

        for t in threads:
            t.start()

        for t in threads:
            t.join(timeout=10)

        # Проверяем, что никто завис
        for i, t in enumerate(threads):
            if t.is_alive():
                self.fail(f"поток {i} не дождался разрешения")

        self.assertLessEqual(peak, limit,
                            f"одновременно внутри было {peak}, лимит {limit}")
        self.assertGreaterEqual(peak, 2,
                               f"параллелизма не случилось вовсе: пик {peak}")

    def test_try_acquire(self):
        s = Semaphore(1)

        self.assertTrue(s.try_acquire(),
                       "TryAcquire при свободном разрешении должен получиться")
        self.assertFalse(s.try_acquire(),
                        "TryAcquire без разрешений должен вернуть false")

        s.release()

        self.assertTrue(s.try_acquire(),
                       "после Release разрешение снова доступно")

    def test_zero_permits(self):
        s = Semaphore(0)

        self.assertFalse(s.try_acquire(),
                        "у семафора на ноль разрешений брать нечего")

        waiting = finished(s.acquire)

        # Acquire не должен пройти на пустом семафоре
        self.assertFalse(waiting.wait(timeout=0.05),
                        "Acquire прошёл на пустом семафоре")

        s.release()

        self.assertTrue(waiting.wait(timeout=2.0),
                       "Acquire не проснулся")

    def test_all_waiters_wake_up(self):
        s = Semaphore(0)
        waiters = 30

        done_events = []

        def waiter_thread():
            s.acquire()
            done_events.append(True)

        threads = [threading.Thread(target=waiter_thread) for _ in range(waiters)]
        for t in threads:
            t.start()

        time.sleep(0.05)

        for _ in range(waiters):
            s.release()

        # Ждём максимум 10 секунд
        deadline = time.time() + 10
        while time.time() < deadline:
            if len(done_events) == waiters:
                break
            time.sleep(0.01)
        else:
            self.fail("не все ждущие проснулись")

        for i, t in enumerate(threads):
            if t.is_alive():
                self.fail(f"поток {i} остался спать навсегда")


# ── Бенчмарки ──────────────────────────────────────────────

def benchmark_acquire_release(iterations=1_000_000):
    s = Semaphore(1)
    start = time.perf_counter()
    for _ in range(iterations):
        s.acquire()
        s.release()
    elapsed = time.perf_counter() - start
    ns_per_op = (elapsed / iterations) * 1e9
    print(f"AcquireRelease:  {iterations:>10} ops  {elapsed:.3f}s  {ns_per_op:.1f} ns/op")


if __name__ == "__main__":
    unittest.main(verbosity=2)