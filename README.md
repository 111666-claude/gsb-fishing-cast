# fishing-cast

钓鱼抛竿结算：池塘表与鱼竿表放在 `sample/` 下按行读入，判定咬钩窗口与力度区间，只用 Python 标准库。

```
python3 -m fishing.cli --sample edge
python3 -m fishing.cli --sample power
python3 -m fishing.cli --sample weight
python3 -m fishing.cli --sample dup
python3 -m fishing.cli --sample work
python3 -m unittest discover -s tests -v
```

## 口径（README 为准）

- **咬钩窗口**：抛竿后经过该鱼的 `bite_ms` 进入咬钩，再经过 `escape_ms` 逃脱；
  收线时刻落在 `[cast + bite, cast + bite + escape]` 内算命中，正好等于上界也算命中。
- **力度匹配**：每条鱼需要的力度是 `rarity × 20`，允许上下浮动 20；收线力度落在闭区间内才算匹配。
- **权重取优**：同一时刻有多条鱼同时满足窗口与力度时，取权重最大的一条，权重相同按 fish_id 升序。
- **幂等**：同一次抛竿（`cast_id`）只结算一次，重复收线返回 None。
- **代价**：判定不许重扫整张池塘表，`work_count()` 不随鱼数乘判定次数增长；10 万条鱼每秒 10 万次收线。

## 输出契约（不改格式）

```
hooked=..
fish=..
work=..
```

## 目录

```
sample/pond.txt      池塘表
sample/rods.txt      鱼竿表
fishing/rules.py     读表与结算规则
fishing/cli.py       命令行入口
tests/test_rules.py  unittest 用例
```
