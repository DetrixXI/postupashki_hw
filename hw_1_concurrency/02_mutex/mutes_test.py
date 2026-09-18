import threading
import time
import unittest
from mutex import Mutex


def finished(f):
    """Запускает f в потоке, возвращает Event, который сработает после завершения."""
    event = threading.Event()
    def wrapper():
        f()
        event.set()
    threading.Thread(target=wrapper, daemon=True).start()
    return event


class TestMutex(unittest.TestCase):

    def test_lock_unlock(self):
        m = Mutex()
        m.lock()
        m.unlock()
        m.lock()
        m.unlock()

    def test_mutual_exclusion(self):
        m = Mutex()
        threads_num = 16
        iterations = 20_000
        counter = 0
        counter_lock = threading.Lock()

        def worker():
            nonlocal counter
            for _ in range(iterations):
                m.lock()
                counter += 1
                m.unlock()

        threads = [threading.Thread(target=worker) for _ in range(threads_num)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(counter, threads_num * iterations,
                         f"счётчик {counter}, ожидалось {threads_num * iterations}")

    def test_only_one_inside(self):
        m = Mutex()
        inside = 0
        bad = False
        bad_lock = threading.Lock()

        def worker():
            nonlocal inside, bad
            for _ in range(3000):
                m.lock()
                inside += 1
                if inside != 1:
                    with bad_lock:
                        bad = True
                inside -= 1
                m.unlock()

        threads = [threading.Thread(target=worker) for _ in range(16)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertFalse(bad, "в критической секции оказалось больше одного потока")

    def test_lock_waits_for_unlock(self):
        m = Mutex()
        m.lock()

        second = finished(lambda: (m.lock(), m.unlock()))

        # Второй lock не должен пройти за 50 мс
        self.assertFalse(second.wait(timeout=0.5),
                        "второй Lock прошёл, пока мьютекс занят")

        m.unlock()

        # После unlock второй lock должен завершиться за 2 секунды
        self.assertTrue(second.wait(timeout=4.0),
                       "второй Lock не проснулся после Unlock")

    def test_every_waiter_wakes_up(self):
        m = Mutex()
        waiters = 50

        m.lock()

        wg_lock = threading.Lock()
        remaining = [waiters]

        def waiter_thread():
            m.lock()
            time.sleep(0.001)
            m.unlock()
            with wg_lock:
                remaining[0] -= 1

        threads = [threading.Thread(target=waiter_thread) for _ in range(waiters)]
        for t in threads:
            t.start()

        time.sleep(0.05)
        m.unlock()

        # Ждём максимум 10 секунд, пока все waiters не проснутся
        deadline = time.time() + 10
        while time.time() < deadline:
            with wg_lock:
                if remaining[0] == 0:
                    break
            time.sleep(0.01)
        else:
            self.fail("часть потоков осталась спать навсегда")

        for t in threads:
            t.join(timeout=10)

    def test_try_lock(self):
        m = Mutex()

        self.assertTrue(m.try_lock(), "TryLock на свободном мьютексе должен получиться")

        result = [None]
        event = threading.Event()

        def try_in_thread():
            result[0] = m.try_lock()
            event.set()

        threading.Thread(target=try_in_thread, daemon=True).start()

        self.assertTrue(event.wait(timeout=5.0),
                       "TryLock заблокировался, а не должен")
        self.assertFalse(result[0],
                        "TryLock на занятом мьютексе должен вернуть False")

        m.unlock()
        self.assertTrue(m.try_lock(), "после Unlock мьютекс свободен")
        m.unlock()

    def test_unlock_without_lock_raises(self):
        m = Mutex()
        with self.assertRaises(RuntimeError):
            m.unlock()

    def test_handoff_under_load(self):
        m = Mutex()
        deadline = time.time() + 0.3
        results = [None] * 8

        def worker(idx):
            passes = 0
            while time.time() < deadline:
                m.lock()
                passes += 1
                m.unlock()
            results[idx] = passes

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
        for t in threads:
            t.start()

        for i, t in enumerate(threads):
            t.join(timeout=5)
            if t.is_alive():
                self.fail(f"поток {i} завис")
            self.assertGreater(results[i], 0, f"поток {i} не получил мьютекс ни разу")


        # Если какой-то поток завис (join по таймауту не завершил работу)
        for i, t in enumerate(threads):
            if t.is_alive():
                self.fail(f"поток {i} завис")
            self.assertGreater(results[i], 0, "горутина не получила мьютекс ни разу")


# ── Бенчмарки ──────────────────────────────────────────────

def benchmark_uncontended(iterations=1_000_000):
    m = Mutex()
    start = time.perf_counter()
    for _ in range(iterations):
        m.lock()
        m.unlock()
    elapsed = time.perf_counter() - start
    ns_per_op = (elapsed / iterations) * 1e9
    print(f"Uncontended:  {iterations:>10} ops  {elapsed:.3f}s  {ns_per_op:.1f} ns/op")


def benchmark_contended(iterations_per_thread=500_000, threads_num=8):
    m = Mutex()
    barrier = threading.Barrier(threads_num)

    def worker():
        barrier.wait()
        for _ in range(iterations_per_thread):
            m.lock()
            m.unlock()

    threads = [threading.Thread(target=worker) for _ in range(threads_num)]
    start = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - start
    total = threads_num * iterations_per_thread
    ns_per_op = (elapsed / total) * 1e9
    print(f"Contended:    {total:>10} ops  {elapsed:.3f}s  {ns_per_op:.1f} ns/op")


def benchmark_stdlib_contended(iterations_per_thread=500_000, threads_num=8):
    m = threading.Lock()
    barrier = threading.Barrier(threads_num)

    def worker():
        barrier.wait()
        for _ in range(iterations_per_thread):
            m.acquire()
            m.release()

    threads = [threading.Thread(target=worker) for _ in range(threads_num)]
    start = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - start
    total = threads_num * iterations_per_thread
    ns_per_op = (elapsed / total) * 1e9
    print(f"Stdlib:       {total:>10} ops  {elapsed:.3f}s  {ns_per_op:.1f} ns/op")


if __name__ == "__main__":
    unittest.main(verbosity=2)
    # benchmark_uncontended()
    # benchmark_contended()
    # benchmark_stdlib_contended()