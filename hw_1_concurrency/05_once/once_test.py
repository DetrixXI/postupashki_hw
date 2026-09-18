import threading
import time
import unittest
from typing import Callable
from once import Once

# Возвращает threading.Event, который взводится по завершении f.

def finished(f: Callable[[], None]) -> threading.Event:
    event = threading.Event()
    def wrapper():
        f()
        event.set()
    threading.Thread(target=wrapper).start()
    return event


# ── тесты ────────────────────────────────────────────────

class TestOnce(unittest.TestCase):

    def test_runs_only_once(self):
        """Do вызывается 10 раз подряд — функция выполняется 1 раз."""
        o = Once()
        calls = [0]

        def f():
            calls[0] += 1

        for _ in range(10):
            o.do(f)

        self.assertEqual(calls[0], 1, f"функция вызвана {calls[0]} раз")

    def test_done(self):
        """Done() возвращает False до Do и True после."""
        o = Once()
        self.assertFalse(o.done(), "до первого Do работа не сделана")

        o.do(lambda: None)

        self.assertTrue(o.done(), "после Do работа сделана")

    def test_concurrent_calls_run_it_once(self):
        """100 потоков одновременно вызывают Do — функция выполняется 1 раз."""
        o = Once()
        calls = [0]
        calls_lock = threading.Lock()

        def increment():
            with calls_lock:
                calls[0] += 1
            time.sleep(0.01)

        threads = []
        for _ in range(100):
            t = threading.Thread(target=o.do, args=(increment,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=10)
            if t.is_alive():
                self.fail("часть потоков зависла в Do")

        self.assertEqual(calls[0], 1, f"функция вызвана {calls[0]} раз")

    def test_do_waits_for_the_winner(self):
        """Второй Do ждёт, пока первый завершит работу, а не возвращается сразу."""
        o = Once()
        state = {"ready": False}

        def first_func():
            time.sleep(0.1)
            state["ready"] = True

        first_done = finished(lambda: o.do(first_func))

        time.sleep(0.01)  # даём первому потоку захватить лок

        def second_call():
            o.do(lambda: None)
            if not state["ready"]:
                self.fail("Do вернулся до того, как работа была закончена")

        second_done = finished(second_call)

        if not first_done.wait(timeout=5):
            self.fail("первый Do завис")
        if not second_done.wait(timeout=5):
            self.fail("второй Do завис")

    def test_panic_counts_as_done(self):
        """Паникнувшая функция всё равно считается выполненной."""
        o = Once()
        calls = [0]

        def panic_func():
            calls[0] += 1
            raise RuntimeError("упало")

        try:
            o.do(panic_func)
        except RuntimeError:
            pass

        o.do(lambda: calls.__setitem__(0, calls[0] + 1))

        self.assertEqual(
            calls[0], 1,
            f"после паники функция вызвана ещё раз: всего {calls[0]}"
        )

    def test_stress(self):
        """300 раундов по 16 потоков — функция выполняется ровно 1 раз в каждом."""
        for round_num in range(300):
            o = Once()
            calls = [0]
            calls_lock = threading.Lock()

            def increment():
                with calls_lock:
                    calls[0] += 1

            threads = []
            for _ in range(16):
                t = threading.Thread(target=o.do, args=(increment,))
                threads.append(t)
                t.start()

            for t in threads:
                t.join()

            self.assertEqual(
                calls[0], 1,
                f"раунд {round_num}: вызовов {calls[0]}"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)