from __future__ import annotations

import numpy as np
import pandas as pd


def _last_percentile(x: np.ndarray) -> float:
    clean = x[np.isfinite(x)]
    return float((clean <= clean[-1]).mean()) if len(clean) else np.nan


def hurst_rs(values: np.ndarray) -> float:
    x = values[np.isfinite(values)]
    if len(x) < 40:
        return np.nan
    lags, rs = [], []
    for size in (10, 20, 40, 80):
        if size > len(x):
            continue
        chunks = [x[i:i + size] for i in range(0, len(x) - size + 1, size)]
        stats = []
        for chunk in chunks:
            dev = chunk - chunk.mean()
            sd = chunk.std(ddof=1)
            if sd > 0:
                stats.append((np.cumsum(dev).max() - np.cumsum(dev).min()) / sd)
        if stats:
            lags.append(np.log(size)); rs.append(np.log(np.mean(stats)))
    return float(np.polyfit(lags, rs, 1)[0]) if len(lags) >= 2 else np.nan


def katz_fd(values: np.ndarray) -> float:
    x = values[np.isfinite(values)]
    if len(x) < 3:
        return np.nan
    points = np.column_stack([np.arange(len(x)), x])
    distances = np.sqrt(np.sum(np.diff(points, axis=0) ** 2, axis=1))
    length = distances.sum()
    diameter = np.sqrt(np.sum((points - points[0]) ** 2, axis=1)).max()
    if length <= 0 or diameter <= 0:
        return np.nan
    return float(np.log10(len(x) - 1) / (np.log10(len(x) - 1) + np.log10(diameter / length)))


def add_timing_features(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy().sort_values("trade_date")
    close = pd.to_numeric(out.get("adjusted_close", out["close"]), errors="coerce")
    for w in (5, 10, 20, 60):
        out[f"ma{w}"] = close.rolling(w, min_periods=max(3, w // 2)).mean()
        out[f"ma_slope_{w}"] = out[f"ma{w}"].pct_change(5) / 5
        out[f"momentum{w}"] = close.pct_change(w)
    out["momentum_acceleration"] = out["momentum5"] - out["momentum20"] / 4
    for w in (20, 60, 120, 250):
        out[f"price_pct_{w}"] = close.rolling(w, min_periods=max(15, w // 2)).apply(_last_percentile, raw=True)
    log_price = np.log(close.where(close > 0))
    out["hurst_rs_120"] = log_price.rolling(120, min_periods=80).apply(hurst_rs, raw=True)
    out["hurst_algorithm"] = "R/S"
    out["fractal_katz_120"] = log_price.rolling(120, min_periods=80).apply(katz_fd, raw=True)
    out["fractal_algorithm"] = "Katz"
    out["rv_term_structure"] = out.get("rv5") / out.get("rv60")
    return out
