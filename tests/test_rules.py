import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fishing.rules import Judge, load_pond, load_rods  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class LoadingTest(unittest.TestCase):
    def test_load_pond_from_sample(self):
        pond = load_pond(os.path.join(HERE, "sample", "pond.txt"))
        self.assertEqual(len(pond), 3)
        self.assertEqual(pond[0]["id"], "sardine")

    def test_load_rods_from_sample(self):
        rods = load_rods(os.path.join(HERE, "sample", "rods.txt"))
        self.assertEqual(rods["carbon"], 80)


class ReelTest(unittest.TestCase):
    def test_reel_inside_window_hooks(self):
        judge = Judge([{"id": "a", "rarity": 1, "weight": 1, "bite": 100, "escape": 200}], {})
        self.assertEqual(judge.reel("c1", "bamboo", 60, 0, 150), "a")

    def test_reel_before_bite_is_none(self):
        judge = Judge([{"id": "a", "rarity": 1, "weight": 1, "bite": 100, "escape": 200}], {})
        self.assertIsNone(judge.reel("c1", "bamboo", 60, 0, 50))

    def test_work_starts_at_zero(self):
        self.assertEqual(Judge([], {}).work_count(), 0)


if __name__ == "__main__":
    unittest.main()
