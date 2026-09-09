from __future__ import annotations

import numpy as np
import pandas as pd

from backtest.factor_test import add_forward_outcomes
from config import EVENT_OFFSETS


EVENT_FEATURES = ["adjusted_close", "momentum20", "open_interest", "volume", "rv20", "skew60", "kurtosis60", "cvar95", "roll_yield_research", "basis_momentum_20", "top20_net", "amihud", "hurst_rs_120", "fractal_katz_120"]


def label_events(frame: pd.DataFrame, drawdown_threshold: float = -.10, rebound_threshold: float = .10) -> pd.DataFrame:
    out = add_forward_outcomes(frame)
    prices = out.groupby("symbol")["adjusted_close"]
    out["future_max_20"] = pd.concat([prices.shift(-i) / out["adjusted_close"] - 1 for i in range(1, 21)], axis=1).max(axis=1)
    out["future_min_20"] = pd.concat([prices.shift(-i) / out["adjusted_close"] - 1 for i in range(1, 21)], axis=1).min(axis=1)
    high, low = out["price_pct_120"] >= .9, out["price_pct_120"] <= .1
    out["event_type"] = np.select(
        [high & (out["future_min_20"] <= drawdown_threshold), high & (out["future_min_20"] > drawdown_threshold) & (out["future_max_20"] > 0),
         low & (out["future_max_20"] >= rebound_threshold), low & (out["future_max_20"] < rebound_threshold) & (out["future_min_20"] < 0)],
        ["TOP", "HIGH_CONTINUE", "BOTTOM", "LOW_CONTINUE"], default="NONE")
    return out


def build_event_windows(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    labeled = label_events(frame)
    events = labeled[labeled["event_type"] != "NONE"].copy()
    events["event_id"] = events["symbol"] + "_" + events["trade_date"].astype(str) + "_" + events["event_type"]
    windows = []
    for symbol, group in labeled.groupby("symbol"):
        group = group.reset_index(drop=True)
        for idx in group.index[group["event_type"] != "NONE"]:
            base = group.loc[idx]
            for offset in EVENT_OFFSETS:
                pos = idx + offset
                if 0 <= pos < len(group):
                    row = {"event_id": f"{symbol}_{base['trade_date']}_{base['event_type']}", "symbol": symbol,
                           "event_date": base["trade_date"], "event_type": base["event_type"], "offset": offset,
                           "observation_date": group.loc[pos, "trade_date"]}
                    row.update({feature: group.loc[pos, feature] if feature in group else np.nan for feature in EVENT_FEATURES})
                    windows.append(row)
    return events, pd.DataFrame(windows)


def top_event_thresholds(events: pd.DataFrame) -> pd.DataFrame:
    cohorts = []
    top = events[events["event_type"] == "TOP"].copy()
    bottom = events[events["event_type"] == "BOTTOM"].copy()
    for threshold in (10, 15, 20):
        cohorts.append(top[top["future_min_20"] <= -threshold / 100].assign(cohort=f"TOP{threshold}", threshold=-threshold / 100))
        cohorts.append(bottom[bottom["future_max_20"] >= threshold / 100].assign(cohort=f"BOTTOM{threshold}", threshold=threshold / 100))
    return pd.concat(cohorts, ignore_index=True) if cohorts else pd.DataFrame()
