from __future__ import annotations

import numpy as np
import pandas as pd


def _last_percentile(x: np.ndarray) -> float:
    clean = x[np.isfinite(x)]
    return float((clean <= clean[-1]).mean()) if len(clean) else np.nan


def add_positioning_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy().sort_values("trade_date")
    oi = pd.to_numeric(out["open_interest"], errors="coerce")
    price = pd.to_numeric(out.get("adjusted_close", out["close"]), errors="coerce")
    out["oi_level"] = oi
    out["oi_change"] = oi.diff()
    out["oi_change_pct"] = oi.pct_change()
    out["oi_percentile_250"] = oi.rolling(250, min_periods=60).apply(_last_percentile, raw=True)
    price_delta, oi_delta = price.diff(), oi.diff()
    out["price_oi_quadrant"] = np.select(
        [(price_delta >= 0) & (oi_delta >= 0), (price_delta >= 0) & (oi_delta < 0),
         (price_delta < 0) & (oi_delta >= 0), (price_delta < 0) & (oi_delta < 0)],
        ["PRICE_UP_OI_UP", "PRICE_UP_OI_DOWN", "PRICE_DOWN_OI_UP", "PRICE_DOWN_OI_DOWN"], default="UNKNOWN")
    out["volume_oi"] = pd.to_numeric(out["volume"], errors="coerce") / oi.where(oi > 0)
    for col in ["roll_yield_user", "roll_yield_research", "spread", "top20_long", "top20_short", "top20_net", "top20_net_ratio"]:
        if col not in out:
            out[col] = np.nan
    if "basis" not in out:
        out["basis"] = np.nan
    out["basis_momentum_20"] = out["basis"].diff(20)
    out["basis_status"] = np.where(out["basis"].notna(), "ok", "missing_spot_benchmark")
    out["crowding_percentile"] = out["top20_net_ratio"].rolling(250, min_periods=60).apply(_last_percentile, raw=True)
    out["positioning_status"] = np.where(out["top20_net"].notna(), "ok", "missing_holdings")
    return out
