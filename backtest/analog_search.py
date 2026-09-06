from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from backtest.event_study import label_events


DEFAULT_FEATURES = ["price_pct_120", "momentum20", "rv20", "oi_change_pct", "cvar95", "skew60", "roll_yield_research", "hurst_rs_120", "fractal_katz_120"]


def find_analogs(frame: pd.DataFrame, symbol: str, as_of=None, n: int = 10) -> pd.DataFrame:
    data = label_events(frame[frame["symbol"] == symbol].copy())
    as_of = pd.Timestamp(as_of) if as_of is not None else data["trade_date"].max()
    usable = [f for f in DEFAULT_FEATURES if data[f].notna().sum() >= 30]
    historical = data[data["trade_date"] < as_of - pd.Timedelta(days=60)].dropna(subset=usable)
    current_rows = data[data["trade_date"] <= as_of].dropna(subset=usable)
    if historical.empty or current_rows.empty:
        return pd.DataFrame()
    current = current_rows.iloc[-1]
    scaler = StandardScaler().fit(historical[usable])
    distances = np.sqrt(((scaler.transform(historical[usable]) - scaler.transform(pd.DataFrame([current[usable]], columns=usable))[0]) ** 2).mean(axis=1))
    result = historical.assign(distance=distances, similarity_score=1 / (1 + distances)).nsmallest(n, "distance")
    columns = ["trade_date", "market_state", "similarity_score", "future_return_5d", "future_return_20d", "future_return_40d", "future_min_20", "future_max_20", "event_type"]
    return result[[c for c in columns if c in result]].rename(columns={"future_min_20": "future_max_drawdown", "future_max_20": "future_max_rebound"})
