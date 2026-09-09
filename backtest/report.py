from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from backtest.event_study import build_event_windows, top_event_thresholds
from backtest.factor_test import conditional_study, quantile_factor_test
from backtest.walk_forward import walk_forward_logistic
from config import DATA, REPORTS, ensure_dirs


FACTORS = ["momentum20", "roll_yield_research", "oi_change_pct", "cvar95", "skew60", "amihud", "top20_net_ratio", "hurst_rs_120", "fractal_katz_120"]


def run_backtests(features_path: Path | None = None) -> dict:
    ensure_dirs()
    path = features_path or DATA / "feature_store" / "features_daily.parquet"
    frame = pd.read_parquet(path)
    target = REPORTS / "backtest"
    target.mkdir(parents=True, exist_ok=True)
    quantiles = quantile_factor_test(frame, FACTORS)
    conditions = conditional_study(frame)
    events, windows = build_event_windows(frame)
    cohorts = top_event_thresholds(events)
    walk = walk_forward_logistic(frame)
    expected_cohorts = [f"{side}{threshold}" for side in ("TOP", "BOTTOM") for threshold in (10, 15, 20)]
    cohort_counts = cohorts["cohort"].value_counts().to_dict() if not cohorts.empty else {}
    threshold_summary = pd.DataFrame([{"cohort": name, "event_count": int(cohort_counts.get(name, 0)),
                                       "threshold": int(name.replace("TOP", "").replace("BOTTOM", "")) / 100}
                                      for name in expected_cohorts])
    for name, data in [("factor_quantiles", quantiles), ("conditional_study", conditions), ("events", events),
                       ("event_windows", windows), ("top_cohorts", cohorts), ("event_threshold_summary", threshold_summary),
                       ("walk_forward", walk)]:
        data.to_csv(target / f"{name}.csv", index=False, encoding="utf-8-sig")
    stability = quantiles.groupby(["factor", "horizon"]).agg(observations=("n", "sum"), mean_return=("mean", "mean"),
                                                               cross_symbol_std=("mean", "std"), positive_groups=("mean", lambda x: float((x > 0).mean()))).reset_index() if not quantiles.empty else pd.DataFrame()
    stability.to_csv(target / "factor_stability.csv", index=False, encoding="utf-8-sig")
    failures = events[events["event_type"].isin(["HIGH_CONTINUE", "LOW_CONTINUE"])][["trade_date", "symbol", "event_type", "future_min_20", "future_max_20"]]
    failures.to_csv(target / "failure_cases.csv", index=False, encoding="utf-8-sig")
    stability_text = "# 因子稳定性报告\n\n## 数据事实\n\n" + (stability.to_markdown(index=False) if not stability.empty else "无可用因子。")
    stability_text += "\n\n## 研究解释\n\n跨品种标准差当前仅有铁矿石，不能解释为跨品种稳定；positive_groups 是分位组方向一致性的描述统计。\n\n## 待验证假设\n\n- 其他品种完成合约治理后复验跨品种稳定性。\n"
    (target / "factor_stability.md").write_text(stability_text, encoding="utf-8")
    failure_counts = failures.groupby(["symbol", "event_type"]).size().reset_index(name="count") if not failures.empty else pd.DataFrame()
    failure_text = "# 失败案例与对照组报告\n\n## 数据事实\n\n" + (failure_counts.to_markdown(index=False) if not failure_counts.empty else "无对照案例。")
    failure_text += "\n\n## 研究解释\n\nHIGH_CONTINUE 与 LOW_CONTINUE 是必要对照组，用于反驳高位必跌、低位必涨的选择偏差。连续日期可能属于同一行情簇，解读事件数时不得等同为独立样本。\n\n## 待验证假设\n\n- 下一版增加事件去簇稳健性检验。\n"
    (target / "failure_cases.md").write_text(failure_text, encoding="utf-8")
    summary = {"data_facts": {"rows": len(frame), "symbols": sorted(frame.symbol.unique().tolist()), "start": str(frame.trade_date.min()), "end": str(frame.trade_date.max())},
               "calculation_results": {"factor_rows": len(quantiles), "event_counts": events.event_type.value_counts().to_dict(), "walk_forward_splits": len(walk),
                                       "walk_forward_auc_valid": int((walk.get("auc_status", pd.Series(dtype=str)) == "ok").sum())},
               "research_interpretation": "回测结果仅为本地历史统计，不构成 BUY/SELL 信号。高位反转与高位继续均纳入，避免成功样本选择偏差。",
               "hypotheses_to_validate": ["引入真实成交额后复验 Amihud", "引入 Top20 后复验拥挤度", "新能源短样本需继续积累"]}
    (target / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    (target / "README.md").write_text(_markdown_summary(summary, stability, failures), encoding="utf-8")
    return summary


def _markdown_summary(summary: dict, stability: pd.DataFrame, failures: pd.DataFrame) -> str:
    counts = summary["calculation_results"]["event_counts"]
    return f"""# 第一版真实历史回测报告

## 数据事实

- 样本：{summary['data_facts']['rows']} 行，{', '.join(summary['data_facts']['symbols'])}
- 区间：{summary['data_facts']['start']} 至 {summary['data_facts']['end']}
- 事件数：{counts}

## 计算结果

- 单因子分位统计：`factor_quantiles.csv`
- 条件研究：`conditional_study.csv`
- Top / High Continue / Bottom / Low Continue：`events.csv`；10%/15%/20% 镜像阈值组见 `top_cohorts.csv`
- Walk-forward：{summary['calculation_results']['walk_forward_splits']} 个模型-窗口结果
- AUC 可评估窗口：{summary['calculation_results']['walk_forward_auc_valid']}；单类别测试窗明确标为 `insufficient_test_classes`，不输出伪 AUC
- 稳定性：`factor_stability.csv`

## 失败案例

已输出 {len(failures)} 条 HIGH_CONTINUE/LOW_CONTINUE 对照案例，见 `failure_cases.csv`。这些不是异常数据，而是用于约束“高位等于顶部”等错误推断的必要反例。

## 研究解释

{summary['research_interpretation']}

## 待验证假设

{chr(10).join('- ' + x for x in summary['hypotheses_to_validate'])}
"""


if __name__ == "__main__":
    print(json.dumps(run_backtests(), ensure_ascii=False, indent=2, default=str))
