from __future__ import annotations

import pandas as pd


def calculate_microstructure(ticks: pd.DataFrame) -> pd.DataFrame:
    required = {"event_time", "bid", "ask", "bid_size", "ask_size", "last_price", "volume", "is_simulated"}
    missing = required - set(ticks.columns)
    if missing:
        raise ValueError(f"Tick data missing: {sorted(missing)}")
    if ticks.empty or ticks["is_simulated"].fillna(True).any():
        raise ValueError("OFI/POC require real tick or minute data; simulated/daily data is forbidden")
    out = ticks.copy().sort_values("event_time")
    out["bid_ask_imbalance"] = (out["bid_size"] - out["ask_size"]) / (out["bid_size"] + out["ask_size"]).replace(0, pd.NA)
    out["ofi"] = out["bid_size"].diff().fillna(0) - out["ask_size"].diff().fillna(0)
    out["mid"] = (out["bid"] + out["ask"]) / 2
    out["price_impact"] = out["mid"].diff() / out["volume"].diff().replace(0, pd.NA)
    return out
