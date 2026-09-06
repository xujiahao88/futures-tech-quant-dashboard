# 第一版真实历史回测报告

## 数据事实

- 样本：10163 行，HC, I, J, JM, LC, PS, RB, SI
- 区间：2020-01-02 00:00:00 至 2026-09-04 00:00:00
- 事件数：{'HIGH_CONTINUE': 1716, 'LOW_CONTINUE': 1585, 'BOTTOM': 283, 'TOP': 260}

## 计算结果

- 单因子分位统计：`factor_quantiles.csv`
- 条件研究：`conditional_study.csv`
- Top / High Continue / Bottom / Low Continue：`events.csv`；10%/15%/20% 镜像阈值组见 `top_cohorts.csv`
- Walk-forward：12 个模型-窗口结果
- AUC 可评估窗口：8；单类别测试窗明确标为 `insufficient_test_classes`，不输出伪 AUC
- 稳定性：`factor_stability.csv`

## 失败案例

已输出 3301 条 HIGH_CONTINUE/LOW_CONTINUE 对照案例，见 `failure_cases.csv`。这些不是异常数据，而是用于约束“高位等于顶部”等错误推断的必要反例。

## 研究解释

回测结果仅为本地历史统计，不构成 BUY/SELL 信号。高位反转与高位继续均纳入，避免成功样本选择偏差。

## 待验证假设

- 引入真实成交额后复验 Amihud
- 引入 Top20 后复验拥挤度
- 新能源短样本需继续积累
