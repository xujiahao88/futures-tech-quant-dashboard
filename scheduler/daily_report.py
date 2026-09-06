from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from backtest.analog_search import find_analogs
from config import DATA, REPORTS, SYMBOLS, ensure_dirs


def _safe(value):
    if value is None or value is pd.NA or (isinstance(value, (float, np.floating)) and np.isnan(value)):
        return None
    if isinstance(value, (pd.Timestamp, np.datetime64)):
        return str(pd.Timestamp(value).date())
    if isinstance(value, np.generic):
        return value.item()
    return value


def generate_daily_report(trade_date: str | None = None) -> tuple[Path, Path]:
    ensure_dirs()
    bars = pd.read_parquet(DATA / "daily" / "daily_bars.parquet")
    features = pd.read_parquet(DATA / "feature_store" / "features_daily.parquet")
    cutoff = pd.Timestamp(trade_date) if trade_date else pd.to_datetime(bars["trade_date"]).max()
    symbol_reports = {}
    for symbol in SYMBOLS:
        bar_rows = bars[(bars.symbol == symbol) & (pd.to_datetime(bars.trade_date) <= cutoff)].sort_values("trade_date")
        if bar_rows.empty:
            symbol_reports[symbol] = {"data_facts": {}, "calculation_results": None,
                                      "research_interpretation": "无可用日线，不作解释。",
                                      "hypotheses_to_validate": ["修复或更换该品种公开数据源"],
                                      "risk_flags": ["MISSING_DAILY_BAR"], "missing_data": ["daily_bar"],
                                      "confidence": "UNAVAILABLE"}
            continue
        bar = bar_rows.iloc[-1]
        feat_rows = features[(features.symbol == symbol) & (pd.to_datetime(features.trade_date) <= cutoff)].sort_values("trade_date")
        feat = feat_rows.iloc[-1] if not feat_rows.empty else None
        analogs = find_analogs(features, symbol, cutoff, 5) if feat is not None else pd.DataFrame()
        symbol_reports[symbol] = {
            "data_facts": {"trade_date": _safe(bar.trade_date), "source": _safe(bar.source), "contract": _safe(bar.contract),
                           "close": _safe(bar.close), "volume": _safe(bar.volume), "open_interest": _safe(bar.open_interest),
                           "roll_flag": _safe(bar.roll_flag), "lineage_status": _safe(bar.lineage_status)},
            "calculation_results": None if feat is None else {
                "survival_layer": {k: _safe(feat.get(k)) for k in ["rv20", "var95", "var99", "cvar95", "cvar99", "skew60", "kurtosis60", "max_drawdown_250", "drawdown_duration", "amihud"]},
                "positioning_layer": {k: _safe(feat.get(k)) for k in ["oi_change", "oi_change_pct", "oi_percentile_250", "price_oi_quadrant", "volume_oi", "roll_yield_user", "roll_yield_research", "basis_momentum_20", "top20_net_ratio"]},
                "timing_layer": {k: _safe(feat.get(k)) for k in ["ma5", "ma20", "ma60", "momentum5", "momentum20", "price_pct_120", "hurst_rs_120", "fractal_katz_120", "rv_term_structure", "relative_strength", "breadth"]},
                "state_classification": _safe(feat.market_state), "state_change": _safe(feat.state_change),
                "historical_analogs": [{k: _safe(v) for k, v in row.items()} for row in analogs.to_dict("records")],
            },
            "research_interpretation": "由黑色期货研究室结合机制、反例与下一验证变量生成；本文件不自动生成方向结论。",
            "hypotheses_to_validate": ["检查期限结构和持仓数据缺口", "核对状态变化是否由真实合约收益驱动"],
            "risk_flags": [] if feat is not None else ["RESEARCH_FEATURES_DISABLED_NO_CONTRACT_LINEAGE"],
            "missing_data": [x for x, ok in {"turnover": pd.notna(bar.get("turnover")), "features": feat is not None}.items() if not ok],
            "confidence": "MEDIUM" if feat is not None else "LOW",
        }
    payload = {"trade_date": str(cutoff.date()), "symbols": symbol_reports,
               "change_vs_yesterday": {s: r.get("calculation_results", {}).get("state_change") if r.get("calculation_results") else None for s, r in symbol_reports.items()},
               "governance": {"statistics_generated_by": "deterministic_feature_engine", "llm_numeric_estimation": False,
                              "evidence_scope": "local_evidence", "provider_continuous_research_disabled_without_lineage": True}}
    target = REPORTS / "daily"
    json_path, md_path = target / f"{cutoff.date()}.json", target / f"{cutoff.date()}.md"
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    lines = [f"# 商品量价日报数据 — {cutoff.date()}", "", "## 数据事实与计算结果", ""]
    for symbol, result in symbol_reports.items():
        facts, calc = result.get("data_facts", {}), result.get("calculation_results")
        lines.append(f"### {symbol} {SYMBOLS[symbol]['name']}")
        lines.append(f"- 数据：{facts.get('contract', 'NA')} 收盘 {facts.get('close', 'NA')}，来源 {facts.get('source', 'NA')}，血缘 {facts.get('lineage_status', 'NA')}")
        lines.append(f"- 计算：状态 {calc.get('state_classification') if calc else '不可用'}；变化 {calc.get('state_change') if calc else '不可用'}")
        lines.append(f"- 风险：{', '.join(result['risk_flags']) or '无额外结构化标记'}；置信度 {result['confidence']}")
        lines.append("")
    lines += ["## 研究解释", "", "数值由确定性计算引擎生成；方向解释、机制、反例与验证变量留给黑色期货研究室。", "", "## 待验证假设", "", "- 接入真实成交额与 Top20 后复验 Amihud 和拥挤度。", "- 接入 CTP/Tick 后再启用 OFI、POC 和价格冲击。"]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


if __name__ == "__main__":
    print([str(x) for x in generate_daily_report()])
