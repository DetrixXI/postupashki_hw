import threading
import time
import unittest
from typing import Callable
from barrier import Barrier


def finished(f: Callable[[], None]) -> threading.Event:
    event = threading.Event()
    def wrapper():
        try:
            f()
        except Exception:
            pass
        event.set()
    threading.Thread(target=wrapper).start()
    return event


class TestBarrier(unittest.TestCase):

    def test_nobody_passes_early(self):
        """2 из 3 участников не проходят барьер; третий открывает путь всем."""
        b = Barrier(3)
        passed = [0]
        passed_lock = threading.Lock()

        def worker():
            b.wait()
            with passed_lock:
                passed[0] += 1

        for _ in range(2):
            threading.Thread(target=worker).start()

        time.sleep(0.1)
        self.assertEqual(
            passed[0], 0,
            f"{passed[0]} участников прошли барьер до прихода всех",
        )

        last = finished(worker)
        self.assertTrue(last.wait(timeout=2), "последний участник не прошёл барьер")

        deadline = time.time() + 2
        while passed[0] != 3 and time.time() < deadline:
            time.sleep(0.001)

        self.assertEqual(passed[0], 3, f"барьер прошли {passed[0]} из 3")

    def test_single_participant(self):
        """Барьер на одного участника не должен блокировать."""
        b = Barrier(1)
        event = finished(b.wait)
        self.assertTrue(event.wait(timeout=1), "барьер на одного не должен блокировать")

    def test_reusable_across_rounds(self):
        """Барьер переиспользуется: 6 потоков × 50 раундов = 300 проходов."""
        parties, rounds = 6, 50
        b = Barrier(parties)
        round_count = [0]
        count_lock = threading.Lock()

        def worker():
            for _ in range(rounds):
                b.wait()
                with count_lock:
                    round_count[0] += 1

        threads = [threading.Thread(target=worker) for _ in range(parties)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)
            if t.is_alive():
                self.fail("барьер завис между раундами")

        self.assertEqual(
            round_count[0], parties * rounds,
            f"проходов {round_count[0]}, ожидалось {parties * rounds}",
        )

    def test_rounds_do_not_overlap(self):
        """Участники следующего раунда не начинают, пока не закончится предыдущий."""
        parties, rounds = 4, 100
        b = Barrier(parties)
        in_round = [0]
        bad = [False]
        count_lock = threading.Lock()

        def worker():
            for _ in range(rounds):
                b.wait()
                with count_lock:
                    in_round[0] += 1
                    if in_round[0] > parties:
                        bad[0] = True
                time.sleep(0.000001)
                with count_lock:
                    in_round[0] -= 1

        threads = [threading.Thread(target=worker) for _ in range(parties)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)
            if t.is_alive():
                self.fail("тест завис")

        self.assertFalse(bad[0], "участники следующего раунда обогнали предыдущий")


if __name__ == "__main__":
    unittest.main(verbosity=2)