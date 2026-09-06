from __future__ import annotations

import numpy as np
import pandas as pd


def _historical_tail(series: pd.Series, window: int, q: float, cvar: bool = False, min_n: int | None = None) -> pd.Series:
    min_n = min_n or max(60, int(1 / (1 - q)) * 5)

    def calc(x: np.ndarray) -> float:
        clean = x[np.isfinite(x)]
        if len(clean) < min_n:
            return np.nan
        threshold = np.quantile(clean, 1 - q)
        return float(clean[clean <= threshold].mean()) if cvar else float(threshold)

    return series.rolling(window, min_periods=min_n).apply(calc, raw=True)


def add_survival_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy().sort_values("trade_date")
    close = pd.to_numeric(out.get("adjusted_close", out["close"]), errors="coerce")
    ret = pd.to_numeric(out.get("analysis_return", close.pct_change()), errors="coerce")
    out["return"] = ret
    prev = close.shift(1)
    adjustment = pd.to_numeric(out.get("adjustment_value", pd.Series(0.0, index=out.index)), errors="coerce").fillna(0)
    adjusted_high = pd.to_numeric(out["high"], errors="coerce") + adjustment
    adjusted_low = pd.to_numeric(out["low"], errors="coerce") + adjustment
    tr = pd.concat([(adjusted_high - adjusted_low).abs(), (adjusted_high - prev).abs(), (adjusted_low - prev).abs()], axis=1).max(axis=1)
    out["atr14"] = tr.rolling(14, min_periods=10).mean()
    for w in (5, 10, 20, 60):
        out[f"rv{w}"] = ret.rolling(w, min_periods=max(5, w // 2)).std(ddof=1) * np.sqrt(252)
    for w in (20, 60, 120, 250):
        out[f"skew{w}"] = ret.rolling(w, min_periods=max(15, w // 2)).skew()
        out[f"kurtosis{w}"] = ret.rolling(w, min_periods=max(15, w // 2)).kurt()
    out["var95"] = _historical_tail(ret, 250, .95, min_n=100)
    out["cvar95"] = _historical_tail(ret, 250, .95, cvar=True, min_n=100)
    out["var99"] = _historical_tail(ret, 500, .99, min_n=500)
    out["cvar99"] = _historical_tail(ret, 500, .99, cvar=True, min_n=500)
    out["var99_sample_status"] = np.where(ret.rolling(500).count() >= 500, "ok", "insufficient_sample")
    peak = close.cummax()
    out["drawdown"] = close / peak - 1
    out["max_drawdown_250"] = out["drawdown"].rolling(250, min_periods=20).min()
    durations, duration = [], 0
    for value in out["drawdown"].fillna(0):
        duration = duration + 1 if value < 0 else 0
        durations.append(duration)
    out["drawdown_duration"] = durations
    turnover = pd.to_numeric(out.get("turnover", pd.Series(index=out.index, dtype=float)), errors="coerce")
    out["amihud"] = ret.abs() / turnover.where(turnover > 0)
    out["amihud_status"] = np.where(turnover.notna() & (turnover > 0), "ok", "missing_turnover")
    for horizon in (20, 60, 120, 250):
        out[f"vol_cone_p10_{horizon}"] = out[f"rv{20 if horizon == 20 else 60}"].rolling(horizon, min_periods=20).quantile(.1)
        out[f"vol_cone_p50_{horizon}"] = out[f"rv{20 if horizon == 20 else 60}"].rolling(horizon, min_periods=20).quantile(.5)
        out[f"vol_cone_p90_{horizon}"] = out[f"rv{20 if horizon == 20 else 60}"].rolling(horizon, min_periods=20).quantile(.9)
    return out
