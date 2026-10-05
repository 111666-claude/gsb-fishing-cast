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
        self.assertEqual(judge.reel("c1", "bamboo", 20, 0, 150), "a")

    def test_reel_before_bite_is_none(self):
        judge = Judge([{"id": "a", "rarity": 1, "weight": 1, "bite": 100, "escape": 200}], {})
        self.assertIsNone(judge.reel("c1", "bamboo", 60, 0, 50))

    def test_work_starts_at_zero(self):
        self.assertEqual(Judge([], {}).work_count(), 0)


def make_judge(*fishes):
    return Judge(list(fishes), {})


def fish(fish_id, rarity=1, weight=1, bite=100, escape=200):
    return {
        "id": fish_id,
        "rarity": rarity,
        "weight": weight,
        "bite": bite,
        "escape": escape,
    }


class WindowEdgeTest(unittest.TestCase):
    """咬钩窗口是 [cast + bite, cast + bite + escape] 闭区间。"""

    def test_reel_at_bite_hooks(self):
        judge = make_judge(fish("a"))
        self.assertEqual(judge.reel("c1", "bamboo", 20, 0, 100), "a")

    def test_reel_at_escape_moment_hooks(self):
        judge = make_judge(fish("a"))
        self.assertEqual(judge.reel("c1", "bamboo", 20, 0, 300), "a")

    def test_reel_one_ms_after_escape_is_none(self):
        judge = make_judge(fish("a"))
        self.assertIsNone(judge.reel("c1", "bamboo", 20, 0, 301))

    def test_reel_one_ms_before_bite_is_none(self):
        judge = make_judge(fish("a"))
        self.assertIsNone(judge.reel("c1", "bamboo", 20, 0, 99))

    def test_window_shifts_with_cast_time(self):
        judge = make_judge(fish("a"))
        self.assertEqual(judge.reel("c1", "bamboo", 20, 1000, 1300), "a")

    def test_zero_escape_hooks_only_at_bite(self):
        judge = make_judge(fish("a", escape=0))
        self.assertEqual(judge.reel("c1", "bamboo", 20, 0, 100), "a")
        self.assertIsNone(judge.reel("c2", "bamboo", 20, 0, 101))


class PowerRangeTest(unittest.TestCase):
    """力度区间是 [rarity * 20 - 20, rarity * 20 + 20] 闭区间。"""

    def test_power_at_lower_bound_hooks(self):
        judge = make_judge(fish("a", rarity=5, bite=0, escape=1000))
        self.assertEqual(judge.reel("c1", "bamboo", 80, 0, 100), "a")

    def test_power_at_upper_bound_hooks(self):
        judge = make_judge(fish("a", rarity=5, bite=0, escape=1000))
        self.assertEqual(judge.reel("c1", "bamboo", 120, 0, 100), "a")

    def test_power_below_range_is_none(self):
        judge = make_judge(fish("a", rarity=5, bite=0, escape=1000))
        self.assertIsNone(judge.reel("c1", "bamboo", 79, 0, 100))

    def test_power_above_range_is_none(self):
        judge = make_judge(fish("a", rarity=5, bite=0, escape=1000))
        self.assertIsNone(judge.reel("c1", "bamboo", 121, 0, 100))

    def test_rarity_one_rejects_power_60(self):
        judge = make_judge(fish("a", rarity=1, bite=0, escape=1000))
        self.assertIsNone(judge.reel("c1", "bamboo", 60, 0, 100))

    def test_rarity_five_rejects_power_50(self):
        judge = make_judge(fish("a", rarity=5, bite=0, escape=1000))
        self.assertIsNone(judge.reel("c1", "bamboo", 50, 0, 100))


class WeightPriorityTest(unittest.TestCase):
    """同一时刻多条命中时取权重最大的，权重相同按 fish_id 升序。"""

    def test_heavier_fish_wins(self):
        judge = make_judge(
            fish("light", weight=1, bite=0, escape=1000),
            fish("heavy", weight=5, bite=0, escape=1000),
        )
        self.assertEqual(judge.reel("c1", "bamboo", 20, 0, 100), "heavy")

    def test_weight_wins_regardless_of_order(self):
        judge = make_judge(
            fish("heavy", weight=5, bite=0, escape=1000),
            fish("light", weight=1, bite=0, escape=1000),
        )
        self.assertEqual(judge.reel("c1", "bamboo", 20, 0, 100), "heavy")

    def test_equal_weight_picks_smaller_fish_id(self):
        judge = make_judge(
            fish("b-fish", weight=5, bite=0, escape=1000),
            fish("a-fish", weight=5, bite=0, escape=1000),
        )
        self.assertEqual(judge.reel("c1", "bamboo", 20, 0, 100), "a-fish")

    def test_weight_compared_across_rarity_buckets(self):
        judge = make_judge(
            fish("rare-light", rarity=2, weight=1, bite=0, escape=1000),
            fish("common-heavy", rarity=1, weight=9, bite=0, escape=1000),
        )
        self.assertEqual(judge.reel("c1", "bamboo", 30, 0, 100), "common-heavy")


class IdempotentTest(unittest.TestCase):
    """同一次抛竿只结算一次，重复收线返回 None。"""

    def test_second_reel_same_cast_is_none(self):
        judge = make_judge(fish("a", bite=0, escape=1000))
        self.assertEqual(judge.reel("c1", "bamboo", 20, 0, 100), "a")
        self.assertIsNone(judge.reel("c1", "bamboo", 20, 0, 100))
        self.assertEqual(len(judge.hooked), 1)

    def test_different_casts_settle_independently(self):
        judge = make_judge(fish("a", bite=0, escape=1000))
        self.assertEqual(judge.reel("c1", "bamboo", 20, 0, 100), "a")
        self.assertEqual(judge.reel("c2", "bamboo", 20, 0, 100), "a")
        self.assertEqual(len(judge.hooked), 2)

    def test_missed_cast_is_still_settled(self):
        judge = make_judge(fish("a", bite=100, escape=200))
        self.assertIsNone(judge.reel("c1", "bamboo", 20, 0, 50))
        self.assertIsNone(judge.reel("c1", "bamboo", 20, 0, 150))
        self.assertEqual(judge.hooked, [])


class WorkCountTest(unittest.TestCase):
    """判定按索引结算，work_count 不随鱼数乘判定次数增长。"""

    def test_work_scales_with_reels_not_pond_size(self):
        pond = [
            fish("f-%d" % index, bite=0, escape=1000)
            for index in range(3000)
        ]
        judge = make_judge(*pond)
        for index in range(3000):
            judge.reel("c-%d" % index, "bamboo", 60, 0, 100)
        self.assertLessEqual(judge.work_count(), 6000)


if __name__ == "__main__":
    unittest.main()
