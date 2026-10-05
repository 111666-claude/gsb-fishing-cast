"""钓鱼判定：按咬钩窗口与力度区间判定命中，同一时刻多条命中按权重取最优。

窗口闭区间 [cast + bite, cast + bite + escape]；力度闭区间
[rarity * 20 - 20, rarity * 20 + 20]。池塘表按 rarity 分桶，每个桶为咬钩
窗口建立扫描线索引，单次收线只做常数次二分查找，不重扫整张池塘表。
"""

import bisect
import heapq


def load_pond(path):
    """读池塘表，每行是 fish_id rarity weight bite_ms escape_ms。"""
    pond = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            fish_id, rarity, weight, bite_ms, escape_ms = line.split()
            pond.append({
                "id": fish_id,
                "rarity": int(rarity),
                "weight": int(weight),
                "bite": int(bite_ms),
                "escape": int(escape_ms),
            })
    return pond


def load_rods(path):
    """读鱼竿表，每行是 rod_id power。"""
    rods = {}
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            rod_id, power = line.split()
            rods[rod_id] = int(power)
    return rods


def power_matches(power, rarity):
    """收线力度落在 rarity * 20 上下浮动 20 的闭区间内才算匹配。"""
    return rarity * 20 - 20 <= power <= rarity * 20 + 20


class _WindowIndex:
    """同一稀有度下所有鱼的咬钩窗口索引。

    把每条鱼的窗口 [bite, bite + escape] 转成 bite 进入、
    bite + escape + 1 离开两个事件，扫描线在每个事件点之间维护当前命中鱼的
    权重堆；查询时刻 d 用二分定位时间段，直接拿到该时刻权重最大
    （权重相同 fish_id 最小）的鱼。
    """

    def __init__(self, fishes):
        starts = {}
        stops = {}
        points = set()
        for seq, fish in enumerate(fishes):
            begin = fish["bite"]
            stop = fish["bite"] + fish["escape"] + 1
            starts.setdefault(begin, []).append((fish, seq))
            stops.setdefault(stop, []).append(seq)
            points.add(begin)
            points.add(stop)
        self.points = sorted(points)
        self.best = []
        heap = []
        removed = set()
        for point in self.points:
            for seq in stops.get(point, ()):
                removed.add(seq)
            for fish, seq in starts.get(point, ()):
                heapq.heappush(
                    heap, (-fish["weight"], fish["id"], seq),
                )
            while heap and heap[0][2] in removed:
                heapq.heappop(heap)
            if heap:
                self.best.append((-heap[0][0], heap[0][1]))
            else:
                self.best.append(None)

    def best_at(self, moment):
        """moment 时刻窗口命中的最优 (weight, fish_id)，没有命中返回 None。"""
        slot = bisect.bisect_right(self.points, moment) - 1
        if slot < 0:
            return None
        return self.best[slot]


def _build_index(pond):
    index = {}
    for fish in pond:
        bucket = index.get(fish["rarity"])
        if bucket is None:
            bucket = []
            index[fish["rarity"]] = bucket
        bucket.append(fish)
    return {
        rarity: _WindowIndex(fishes)
        for rarity, fishes in index.items()
    }


class Judge:
    """抛竿结算台账。给 pond 重新赋值会自动重建索引。"""

    def __init__(self, pond, rods):
        self.rods = rods
        self.hooked = []
        self.work = 0
        self._settled = set()
        self.pond = pond

    @property
    def pond(self):
        return self._pond

    @pond.setter
    def pond(self, value):
        self._pond = value
        self._index = _build_index(value)

    def reel(self, cast_id, rod_id, power, cast_ms, reel_ms):
        """收线结算，返回命中的鱼 id，没命中返回 None。

        同一 cast_id 只结算一次，重复收线直接返回 None。力度匹配的稀有度
        至多三种，每桶一次二分查询，不随鱼数线性扫描。
        """
        if cast_id in self._settled:
            return None
        self._settled.add(cast_id)
        self.work += 1
        moment = reel_ms - cast_ms
        low = -((20 - power) // 20)
        high = (power + 20) // 20
        best = None
        for rarity in range(max(low, 0), high + 1):
            window = self._index.get(rarity)
            if window is None:
                continue
            entry = window.best_at(moment)
            if entry is None:
                continue
            if best is None or (-entry[0], entry[1]) < (-best[0], best[1]):
                best = entry
        if best is None:
            return None
        self.hooked.append(cast_id)
        return best[1]

    def work_count(self):
        return self.work
