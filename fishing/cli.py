"""命令行入口：跑钓鱼判定样例（池塘与鱼竿都从 sample 目录读取）。"""

import argparse
import os

from .rules import Judge, load_pond, load_rods

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POND = os.path.join(HERE, "sample", "pond.txt")
RODS = os.path.join(HERE, "sample", "rods.txt")


def build_parser():
    parser = argparse.ArgumentParser(prog="fishing-cast", description="钓鱼抛竿结算")
    parser.add_argument("--pond", default=POND, help="池塘表路径")
    parser.add_argument("--rods", default=RODS, help="鱼竿表路径")
    parser.add_argument("--sample", default="edge", help="edge / power / weight / dup / work")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    judge = Judge(load_pond(args.pond), load_rods(args.rods))
    if args.sample == "edge":
        # 金枪鱼咬钩 100ms、逃逸 200ms，正好在第 300ms 收线。
        print("hooked=%s" % judge.reel("c1", "bamboo", 100, 0, 300))
    elif args.sample == "power":
        # 稀有度 5 的鱼需要 80 到 120 的力度。
        judge.pond = [{"id": "golden-koi", "rarity": 5, "weight": 1, "bite": 0, "escape": 1000}]
        print("hooked=%s" % judge.reel("c1", "bamboo", 50, 300, 500))
    elif args.sample == "weight":
        judge.pond = [
            {"id": "sardine", "rarity": 1, "weight": 1, "bite": 0, "escape": 1000},
            {"id": "sea-bass", "rarity": 1, "weight": 5, "bite": 0, "escape": 1000},
        ]
        print("fish=%s" % judge.reel("c1", "bamboo", 60, 0, 100))
    elif args.sample == "dup":
        judge.pond = [{"id": "sardine", "rarity": 1, "weight": 1, "bite": 0, "escape": 1000}]
        judge.reel("c1", "bamboo", 60, 0, 100)
        judge.reel("c1", "bamboo", 60, 0, 100)
        print("hooks=%d" % len(judge.hooked))
    elif args.sample == "work":
        judge.pond = [
            {"id": "f-%d" % index, "rarity": 1, "weight": 1, "bite": 0, "escape": 1000}
            for index in range(3000)
        ]
        for index in range(3000):
            judge.reel("c-%d" % index, "bamboo", 60, 0, 100)
        print("work=%d" % judge.work_count())
    else:
        raise SystemExit("需要 --sample edge|power|weight|dup|work")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
