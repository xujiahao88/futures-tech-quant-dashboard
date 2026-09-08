from __future__ import annotations

import numpy as np
import pandas as pd


HORIZONS = (1, 5, 10, 20, 40)


def _causal_bucket(series: pd.Series, bins: int) -> pd.Series:
    percentile = series.expanding(min_periods=max(20, bins * 4)).apply(
        lambda x: float((x[np.isfinite(x)] <= x[-1]).mean()) if np.isfinite(x[-1]) else np.nan, raw=True)
    return np.ceil(percentile * bins).clip(1, bins)


def add_forward_outcomes(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy().sort_values(["symbol", "trade_date"])
    for horizon in HORIZONS:
        out[f"future_return_{horizon}d"] = out.groupby("symbol")["adjusted_close"].shift(-horizon) / out["adjusted_close"] - 1
        future = [out.groupby("symbol")["adjusted_close"].shift(-i) / out["adjusted_close"] - 1 for i in range(1, horizon + 1)]
        stack = pd.concat(future, axis=1)
        out[f"mae_{horizon}d"] = stack.min(axis=1)
        out[f"mfe_{horizon}d"] = stack.max(axis=1)
    return out


def quantile_factor_test(frame: pd.DataFrame, factors: list[str], bins: int = 5) -> pd.DataFrame:
    data = add_forward_outcomes(frame)
    results = []
    for factor in factors:
        if factor not in data or data[factor].notna().sum() < bins * 10:
            continue
        work = data[["trade_date", "symbol", factor] + [f"future_return_{h}d" for h in HORIZONS] + [f"mae_{h}d" for h in HORIZONS] + [f"mfe_{h}d" for h in HORIZONS]].copy()
        work["quantile"] = work.groupby("symbol")[factor].transform(lambda s: _causal_bucket(s, bins))
        for (symbol, quantile), group in work.groupby(["symbol", "quantile"]):
            for horizon in HORIZONS:
                returns = group[f"future_return_{horizon}d"].dropna()
                if returns.empty:
                    continue
                results.append({
                    "factor": factor, "symbol": symbol, "quantile": int(quantile), "horizon": horizon,
                    "n": len(returns), "mean": returns.mean(), "median": returns.median(),
                    "win_rate": (returns > 0).mean(),
                    "max_adverse_excursion": group.loc[returns.index, f"mae_{horizon}d"].mean(),
                    "max_favorable_excursion": group.loc[returns.index, f"mfe_{horizon}d"].mean(),
                    "tail_loss_p05": returns.quantile(.05), "evidence_type": "local_evidence",
                })
    return pd.DataFrame(results)


def conditional_study(frame: pd.DataFrame) -> pd.DataFrame:
    data = add_forward_outcomes(frame)
    conditions = {
        "HIGH_PRICE_CVAR_HIGH": (data["price_pct_120"] >= .9) & (data["cvar95"] <= data.groupby("symbol")["cvar95"].transform(lambda s: s.rolling(250, min_periods=60).quantile(.2))),
        "HIGH_PRICE_OI_DECLINE": (data["price_pct_120"] >= .9) & (data["oi_change_pct"] < 0),
        "HIGH_PRICE_BACK_NARROWING": (data["price_pct_120"] >= .9) & (data.groupby("symbol")["roll_yield_research"].diff(20) < 0),
        "HIGH_PRICE_SKEW_DETERIORATION": (data["price_pct_120"] >= .9) & (data.groupby("symbol")["skew60"].diff(20) < 0),
        "HIGH_PRICE_CROWDING_EXTREME": (data["price_pct_120"] >= .9) & (data["crowding_percentile"] >= .9),
    }
    rows = []
    for name, mask in conditions.items():
        for symbol, group in data[mask].groupby("symbol"):
            for horizon in HORIZONS:
                series = group[f"future_return_{horizon}d"].dropna()
                if not series.empty:
                    rows.append({"condition": name, "symbol": symbol, "horizon": horizon, "n": len(series),
                                 "mean": series.mean(), "median": series.median(), "win_rate": (series > 0).mean(),
                                 "tail_loss_p05": series.quantile(.05), "evidence_type": "local_evidence"})
    return pd.DataFrame(rows)
