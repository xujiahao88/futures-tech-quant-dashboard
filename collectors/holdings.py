from __future__ import annotations

import pandas as pd


REQUIRED = ["trade_date", "symbol", "contract", "top20_long", "top20_short"]


def normalize_holdings(frame: pd.DataFrame) -> pd.DataFrame:
    missing = set(REQUIRED) - set(frame.columns)
    if missing:
        raise ValueError(f"Holdings missing fields: {sorted(missing)}")
    out = frame.copy()
    out["top20_net"] = out["top20_long"] - out["top20_short"]
    denom = out["top20_long"] + out["top20_short"]
    out["top20_net_ratio"] = out["top20_net"] / denom.where(denom != 0)
    return out
