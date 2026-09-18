# 
# !!!ТЕСТЫ ПЕРЕПИСАНЫ С ГО НА ПИТОН ИИ-ШКОЙ!!!
# 
import threading
import time
import unittest
from spinlock import Spinlock, TTAS
# Предполагается, что Spinlock и TTAS импортированы.
# Оба класса должны иметь единый интерфейс: lock(), unlock(), try_lock()


def each(test_case, f):
    """Запускает функцию f для Spinlock и TTAS — аналог Go-функции each()."""
    for name, lock_class in [("Spinlock", Spinlock), ("TTAS", TTAS)]:
        with test_case.subTest(lock=name):
            f(test_case, lock_class())


def finished(f):
    """
    Запускает f в отдельном потоке, возвращает threading.Event,
    который будет установлен, когда f завершится.
    Аналог Go-функции finished(), возвращающей <-chan struct{}.
    """
    event = threading.Event()
    def wrapper():
        f()
        event.set()
    threading.Thread(target=wrapper, daemon=True).start()
    return event


class TestSpinlocks(unittest.TestCase):

    def test_lock_unlock(self):
        def run(test, l):
            l.lock()
            l.unlock()
            l.lock()
            l.unlock()
        each(self, run)

    def test_mutual_exclusion(self):
        def run(test, l):
            threads_num = 8
            iterations = 20_000
            counter = 0

            def worker():
                nonlocal counter
                for _ in range(iterations):
                    l.lock()
                    counter += 1
                    l.unlock()

            threads = [threading.Thread(target=worker) for _ in range(threads_num)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            test.assertEqual(counter, threads_num * iterations,
                             f"счётчик {counter}, ожидалось {threads_num * iterations}")
        each(self, run)

    def test_only_one_inside(self):
        def run(test, l):
            inside = 0
            bad = False

            def worker():
                nonlocal inside, bad
                for _ in range(2000):
                    l.lock()
                    inside += 1
                    if inside != 1:
                        bad = True
                    inside -= 1
                    l.unlock()

            threads = [threading.Thread(target=worker) for _ in range(8)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            test.assertFalse(bad, "в критической секции оказалось больше одного потока")
        each(self, run)

    def test_try_lock(self):
        def run(test, l):
            test.assertTrue(l.try_lock(), "TryLock на свободном замке должен получиться")

            # Запускаем try_lock в отдельном потоке — замок уже занят
            result = [None]
            event = threading.Event()

            def try_in_thread():
                result[0] = l.try_lock()
                event.set()

            threading.Thread(target=try_in_thread, daemon=True).start()

            # Ждём не более 1 секунды (аналог select + time.After)
            if not event.wait(timeout=1.0):
                test.fail("TryLock заблокировался, а не должен")
            test.assertFalse(result[0], "TryLock на занятом замке должен вернуть False")

            l.unlock()
            test.assertTrue(l.try_lock(), "после Unlock замок снова свободен")
            l.unlock()
        each(self, run)

    def test_lock_waits_for_unlock(self):
        def run(test, l):
            l.lock()

            # Второй lock в другом потоке — должен заблокироваться
            second = finished(lambda: (l.lock(), l.unlock()))

            # За 50 мс второй lock не должен пройти
            if second.wait(timeout=0.05):
                test.fail("второй Lock прошёл, пока замок занят")

            l.unlock()

            # После unlock второй lock должен завершиться за 2 секунды
            if not second.wait(timeout=2.0):
                test.fail("второй Lock не проснулся после Unlock")
        each(self, run)

    def test_unlock_without_lock_raises(self):
        def run(test, l):
            with test.assertRaises(RuntimeError, msg="Unlock без Lock должен вызвать ошибку"):
                l.unlock()
        each(self, run)


# ── Бенчмарки ──────────────────────────────────────────────

def benchmark_uncontended():
    """Аналог Go BenchmarkUncontended: один поток, lock/unlock в цикле."""
    l = Spinlock()
    iterations = 1_000_000
    start = time.perf_counter()
    for _ in range(iterations):
        l.lock()
        l.unlock()
    elapsed = time.perf_counter() - start
    ns_per_op = (elapsed / iterations) * 1e9
    print(f"BenchmarkUncontended: {iterations} ops, {elapsed:.3f}s, {ns_per_op:.1f} ns/op")


def benchmark_contended():
    """Аналог Go BenchmarkContended: несколько потоков борются за один лок."""
    l = Spinlock()
    threads_num = 8
    iterations_per_thread = 100_000
    barrier = threading.Barrier(threads_num)

    def worker():
        barrier.wait()
        for _ in range(iterations_per_thread):
            l.lock()
            l.unlock()

    threads = [threading.Thread(target=worker) for _ in range(threads_num)]
    start = time.perf_counter()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    elapsed = time.perf_counter() - start
    total_ops = threads_num * iterations_per_thread
    ns_per_op = (elapsed / total_ops) * 1e9
    print(f"BenchmarkContended: {total_ops} ops, {elapsed:.3f}s, {ns_per_op:.1f} ns/op")


if __name__ == "__main__":
    unittest.main()
    # benchmark_uncontended()
    # benchmark_contended()