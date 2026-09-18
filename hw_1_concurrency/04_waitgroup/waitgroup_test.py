import threading
import time
import unittest
from waitgroup import waitgroup as WaitGroup


import threading
import time
import unittest


def finished(f):
    event = threading.Event()
    def wrapper():
        f()
        event.set()
    threading.Thread(target=wrapper, daemon=True).start()
    return event


class TestWaitGroup(unittest.TestCase):

    def test_wait_on_zero_returns_at_once(self):
        wg = WaitGroup(0)
        event = finished(wg.wait)

        if not event.wait(timeout=1.0):
            self.fail("Wait на нулевом счётчике не должен блокировать")

    def test_waits_for_everyone(self):
        wg = WaitGroup(0)
        done_counter = [0]
        done_lock = threading.Lock()

        workers = 20
        wg.add(workers)

        def worker():
            time.sleep(0.02)
            with done_lock:
                done_counter[0] += 1
            wg.done()

        for _ in range(workers):
            threading.Thread(target=worker, daemon=True).start()

        event = finished(wg.wait)

        if not event.wait(timeout=5.0):
            self.fail("Wait не дождался")

        got = done_counter[0]
        if got != workers:
            self.fail(f"Wait вернулся, когда закончили только {got} из {workers}")

    def test_many_waiters(self):
        wg = WaitGroup(0)
        wg.add(1)

        waiters_done = []
        waiters_lock = threading.Lock()

        def waiter():
            wg.wait()
            with waiters_lock:
                waiters_done.append(1)

        for _ in range(30):
            threading.Thread(target=waiter, daemon=True).start()

        time.sleep(0.05)
        wg.done()

        deadline = time.time() + 5.0
        while time.time() < deadline:
            with waiters_lock:
                if len(waiters_done) == 30:
                    break
            time.sleep(0.01)
        else:
            self.fail("не все ожидающие проснулись")

    def test_wait_blocks_until_done(self):
        wg = WaitGroup(0)
        wg.add(1)

        waiting = finished(wg.wait)

        if waiting.wait(timeout=0.05):
            self.fail("Wait вернулся раньше времени")

        wg.done()

        if not waiting.wait(timeout=2.0):
            self.fail("Wait не проснулся после Done")

    def test_reuse(self):
        wg = WaitGroup(0)

        for round_num in range(5):
            wg.add(4)
            for _ in range(4):
                threading.Thread(target=wg.done, daemon=True).start()

            event = finished(wg.wait)

            if not event.wait(timeout=2.0):
                self.fail(f"раунд {round_num}: Wait завис")

    def test_negative_counter_panics(self):
        wg = WaitGroup(0)

        with self.assertRaises(Exception, msg="уход счётчика в минус должен вызывать ошибку"):
            wg.done()

    def test_stress(self):
        for round_num in range(200):
            wg = WaitGroup(0)
            counter = [0]
            counter_lock = threading.Lock()

            wg.add(8)

            def worker():
                with counter_lock:
                    counter[0] += 1
                wg.done()

            for _ in range(8):
                threading.Thread(target=worker, daemon=True).start()

            event = finished(wg.wait)

            if not event.wait(timeout=5.0):
                self.fail(f"раунд {round_num} завис")

            if counter[0] != 8:
                self.fail(f"раунд {round_num}: счётчик {counter[0]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
