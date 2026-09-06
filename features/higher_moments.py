from __future__ import annotations

import numpy as np
import pandas as pd


def add_co_moments(asset: pd.DataFrame, benchmark: pd.DataFrame, benchmark_name: str, window: int = 250) -> pd.DataFrame:
    if not benchmark_name:
        raise ValueError("benchmark_name is mandatory; silent benchmark substitution is forbidden")
    merged = asset.merge(benchmark[["trade_date", "return"]].rename(columns={"return": "benchmark_return"}), on="trade_date", how="left")

    def co_skew(x):
        a, b = x[:, 0], x[:, 1]
        mask = np.isfinite(a) & np.isfinite(b)
        a, b = a[mask], b[mask]
        return np.mean((a - a.mean()) * (b - b.mean()) ** 2) / (a.std() * b.std() ** 2) if len(a) >= 100 and a.std() > 0 and b.std() > 0 else np.nan

    def co_kurt(x):
        a, b = x[:, 0], x[:, 1]
        mask = np.isfinite(a) & np.isfinite(b)
        a, b = a[mask], b[mask]
        return np.mean((a - a.mean()) * (b - b.mean()) ** 3) / (a.std() * b.std() ** 3) if len(a) >= 100 and a.std() > 0 and b.std() > 0 else np.nan

    pair = merged[["return", "benchmark_return"]]
    merged["co_skewness"] = pair.rolling(window, min_periods=100).apply(lambda col: np.nan, raw=True)["return"]
    merged["co_kurtosis"] = np.nan
    # DataFrame rolling does not pass a 2D array; calculate explicit windows.
    for i in range(window - 1, len(merged)):
        values = pair.iloc[i - window + 1:i + 1].to_numpy(float)
        merged.loc[merged.index[i], "co_skewness"] = co_skew(values)
        merged.loc[merged.index[i], "co_kurtosis"] = co_kurt(values)
    merged["benchmark_name"] = benchmark_name
    return merged
