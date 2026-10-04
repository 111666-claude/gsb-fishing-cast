"""钓鱼判定：按咬钩窗口与力度区间判定命中，同一时刻多条命中按权重取最优。

缺陷：咬钩窗口上界用开区间、力度区间不看稀有度、命中取登记顺序第一条而不是权重最大的、
同一次抛竿重复收线会重复结算、每次判定重扫整张池塘表。
"""


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


class Judge:
    """抛竿结算台账。"""

    def __init__(self, pond, rods):
        self.pond = pond
        self.rods = rods
        self.hooked = []
        self.work = 0

    def reel(self, cast_id, rod_id, power, cast_ms, reel_ms):
        """收线结算，返回命中的鱼 id，没命中返回 None。

        缺陷：窗口上界用小于、力度区间不看稀有度、取登记顺序第一条、重复 cast_id 重复结算、全扫池塘表。
        """
        self.work += len(self.pond)
        for fish in self.pond:
            if cast_ms + fish["bite"] > reel_ms:
                continue
            if reel_ms >= cast_ms + fish["bite"] + fish["escape"]:
                continue
            if 40 <= power <= 80:
                self.hooked.append(cast_id)
                return fish["id"]
        return None

    def work_count(self):
        return self.work
