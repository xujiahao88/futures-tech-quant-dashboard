# 失败案例与对照组报告

## 数据事实

| symbol   | event_type    |   count |
|:---------|:--------------|--------:|
| HC       | HIGH_CONTINUE |     292 |
| HC       | LOW_CONTINUE  |     169 |
| I        | HIGH_CONTINUE |     450 |
| I        | LOW_CONTINUE  |     107 |
| J        | HIGH_CONTINUE |     291 |
| J        | LOW_CONTINUE  |     201 |
| JM       | HIGH_CONTINUE |     307 |
| JM       | LOW_CONTINUE  |     242 |
| LC       | HIGH_CONTINUE |      63 |
| LC       | LOW_CONTINUE  |     188 |
| PS       | HIGH_CONTINUE |      45 |
| PS       | LOW_CONTINUE  |     119 |
| RB       | HIGH_CONTINUE |     268 |
| RB       | LOW_CONTINUE  |     223 |
| SI       | LOW_CONTINUE  |     336 |

## 研究解释

HIGH_CONTINUE 与 LOW_CONTINUE 是必要对照组，用于反驳高位必跌、低位必涨的选择偏差。连续日期可能属于同一行情簇，解读事件数时不得等同为独立样本。

## 待验证假设

- 下一版增加事件去簇稳健性检验。
