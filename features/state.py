from __future__ import annotations

import numpy as np
import pandas as pd


def classify_state(row: pd.Series) -> str:
    price = row.get("price_pct_120", np.nan)
    mom = row.get("momentum20", np.nan)
    accel = row.get("momentum_acceleration", np.nan)
    oi = row.get("oi_change_pct", np.nan)
    rv = row.get("rv20", np.nan)
    rv60 = row.get("rv60", np.nan)
    skew = row.get("skew60", np.nan)
    if pd.isna(price) or pd.isna(mom):
        return "TRANSITION"
    if price >= .9 and mom > 0 and accel < 0 and rv > rv60:
        return "HIGH_FRAGILITY"
    if mom > .04 and oi < 0 and skew > .3:
        return "SHORT_SQUEEZE"
    if mom < -.04 and oi < 0 and skew < -.3:
        return "LONG_LIQUIDATION"
    if mom < 0 and oi > 0:
        return "NEW_SHORT_TREND"
    if price <= .1 and mom < 0 and accel > 0:
        return "POTENTIAL_BOTTOM"
    if rv > rv60 * 1.4 and abs(mom) < .02:
        return "HIGH_NOISE"
    if mom > 0 and row.get("ma_slope_20", 0) > 0:
        return "HEALTHY_TREND"
    return "TRANSITION"


def add_states(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["market_state"] = out.apply(classify_state, axis=1)
    out["previous_state"] = out.groupby("symbol")["market_state"].shift(1)
    out["state_change"] = np.where(
        out["previous_state"].notna() & (out["previous_state"] != out["market_state"]),
        out["previous_state"] + " -> " + out["market_state"], "UNCHANGED")
    return out
