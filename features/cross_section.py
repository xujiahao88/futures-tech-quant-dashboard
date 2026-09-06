from __future__ import annotations

import pandas as pd

from config import SYMBOLS


def add_cross_section_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["group"] = out["symbol"].map({s: cfg["group"] for s, cfg in SYMBOLS.items()})
    out["relative_strength"] = out.groupby("trade_date")["momentum20"].rank(pct=True)
    trend_up = (out["momentum20"] > 0).astype(float)
    out["breadth"] = trend_up.groupby([out["trade_date"], out["group"]]).transform("mean")
    date_count = out.groupby("trade_date")["symbol"].transform("nunique")
    group_count = out.groupby(["trade_date", "group"])["symbol"].transform("nunique")
    out.loc[date_count < 3, "relative_strength"] = pd.NA
    out.loc[group_count < 3, "breadth"] = pd.NA
    out["black_breadth"] = out["breadth"].where(out["group"] == "black")
    out["new_energy_breadth"] = out["breadth"].where(out["group"] == "new_energy")
    return out
