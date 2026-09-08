from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd


def run_quality_checks(bars: pd.DataFrame, features: pd.DataFrame | None = None) -> pd.DataFrame:
    rows = []
    now = datetime.now(timezone.utc)

    def add(symbol, dataset, severity, name, details):
        rows.append({"checked_at": now, "symbol": symbol, "dataset": dataset, "severity": severity, "check_name": name, "details": details})

    expected = {"trade_date", "symbol", "contract", "open", "high", "low", "close", "volume", "open_interest", "source"}
    for symbol, group in bars.groupby("symbol"):
        missing_cols = sorted(expected - set(group.columns))
        add(symbol, "daily_bars", "ERROR" if missing_cols else "OK", "required_columns", ",".join(missing_cols) or "complete")
        duplicates = int(group.duplicated(["trade_date", "symbol"]).sum())
        add(symbol, "daily_bars", "ERROR" if duplicates else "OK", "duplicate_keys", str(duplicates))
        invalid_ohlc = int(((group["high"] < group[["open", "close", "low"]].max(axis=1)) | (group["low"] > group[["open", "close", "high"]].min(axis=1))).sum())
        add(symbol, "daily_bars", "ERROR" if invalid_ohlc else "OK", "ohlc_integrity", str(invalid_ohlc))
        latest = pd.to_datetime(group["trade_date"]).max()
        shanghai_today = pd.Timestamp(datetime.now(ZoneInfo("Asia/Shanghai")).date())
        stale_days = max(0, (shanghai_today - latest.normalize()).days)
        business_lag = int(np.busday_count(
            (latest.normalize() + pd.Timedelta(days=1)).date(),
            (shanghai_today + pd.Timedelta(days=1)).date(),
        )) if latest.normalize() < shanghai_today else 0
        add(symbol, "daily_bars", "WARN" if business_lag > 1 else "OK", "freshness",
            f"latest={latest.date()}, business_days_lag={business_lag}, calendar_days={stale_days}")
        lineage = set(group.get("lineage_status", pd.Series(dtype=str)).dropna().astype(str))
        add(symbol, "daily_bars", "WARN" if "provider_unavailable" in lineage else "OK", "contract_lineage", ",".join(sorted(lineage)) or "missing")
        roll_count = int(group.get("roll_flag", pd.Series(False, index=group.index)).fillna(False).sum())
        add(symbol, "daily_bars", "OK", "contract_rolls", str(roll_count))
        missing = [c for c in ("turnover",) if c in group and group[c].isna().all()]
        add(symbol, "daily_bars", "WARN" if missing else "OK", "missing_fields", ",".join(missing) or "none")
        clean_count = int((group.get("cleaning_flags", pd.Series("none", index=group.index)) != "none").sum())
        add(symbol, "daily_bars", "WARN" if clean_count else "OK", "cleaning_adjustments", str(clean_count))
        eligible = group.get("research_eligible", pd.Series(False, index=group.index)).fillna(False).astype(bool)
        add(symbol, "daily_bars", "WARN" if not eligible.all() else "OK", "research_eligibility",
            f"eligible_rows={int(eligible.sum())}/{len(group)}")
    if features is not None and not features.empty:
        for symbol, group in features.groupby("symbol"):
            status = group.iloc[-1].get("var99_sample_status", "missing")
            add(symbol, "features_daily", "WARN" if status != "ok" else "OK", "sample_insufficiency", f"var99={status}")
            for col in ["amihud", "top20_net_ratio", "roll_yield_research"]:
                if col in group and group[col].isna().all():
                    add(symbol, "features_daily", "WARN", f"feature_missing_{col}", "upstream data unavailable; no proxy generated")
    return pd.DataFrame(rows)
