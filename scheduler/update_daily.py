from __future__ import annotations

import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from collectors.api_daily import SinaDailyCollector, contract_universe, save_result
from collectors.main_continuous import build_main_continuous
from collectors.term_structure import build_term_structure
from config import DATA, REPORTS, SYMBOLS, ensure_dirs
from data_quality import run_quality_checks
from database.db import Database
from features.feature_pipeline import calculate_features


def _provider_to_bar(frame: pd.DataFrame) -> pd.DataFrame:
    out = frame.copy()
    out["main_contract"] = out["contract"]
    out["roll_flag"] = pd.NA
    out["previous_contract"] = pd.NA
    out["next_contract"] = pd.NA
    out["adjustment_method"] = "provider_unknown"
    out["adjustment_value"] = np.nan
    out["adjusted_close"] = out["close"]
    out["true_contract_return"] = np.nan
    out["analysis_return"] = np.nan
    out["research_eligible"] = False
    return out


def _clean_bars(frame: pd.DataFrame) -> pd.DataFrame:
    """Repair mechanical provider violations while preserving flags and raw cache."""
    out = frame.copy()
    if "cleaning_flags" not in out:
        out["cleaning_flags"] = "none"
    else:
        out["cleaning_flags"] = out["cleaning_flags"].fillna("none")
    floor = out[["open", "close", "low"]].min(axis=1)
    ceiling = out[["open", "close", "high"]].max(axis=1)
    low_bad, high_bad = out["low"] > floor, out["high"] < ceiling
    out.loc[low_bad, "low"] = floor[low_bad]
    out.loc[high_bad, "high"] = ceiling[high_bad]
    out.loc[low_bad | high_bad, "cleaning_flags"] = "ohlc_bounds_corrected"
    settle_zero = pd.to_numeric(out["settlement"], errors="coerce") <= 0
    out.loc[settle_zero, "settlement"] = np.nan
    out.loc[settle_zero & (out["cleaning_flags"] == "none"), "cleaning_flags"] = "settlement_nonpositive_to_null"
    out.loc[settle_zero & (out["cleaning_flags"] != "none") & ~out["cleaning_flags"].str.contains("settlement"), "cleaning_flags"] += ";settlement_nonpositive_to_null"
    return out


def _overlay_cached_official_latest(frame: pd.DataFrame) -> pd.DataFrame:
    """Use the best-volume official contract for the cached latest EOD date."""
    out = frame.copy()
    for exchange in ("SHFE", "GFEX"):
        files = sorted((DATA / "raw" / "official").glob(f"{exchange}_*.parquet"))
        if not files:
            continue
        official = pd.read_parquet(files[-1]).rename(columns={"date": "trade_date", "settle": "settlement"})
        official["trade_date"] = pd.to_datetime(official["trade_date"])
        official["variety"] = official["variety"].astype(str).str.upper()
        official["volume"] = pd.to_numeric(official["volume"], errors="coerce")
        official["open_interest"] = pd.to_numeric(official["open_interest"], errors="coerce")
        leaders = official[official["variety"].isin(SYMBOLS)].sort_values(
            ["trade_date", "variety", "volume", "open_interest"], ascending=[True, True, False, False]
        ).groupby(["trade_date", "variety"], as_index=False).head(1)
        for _, row in leaders.iterrows():
            symbol, trade_date = row["variety"], row["trade_date"]
            if SYMBOLS[symbol]["exchange"] != exchange:
                continue
            mask = (out["symbol"] == symbol) & (pd.to_datetime(out["trade_date"]) == trade_date)
            if not mask.any():
                continue
            for col in ["open", "high", "low", "close", "settlement", "volume", "turnover", "open_interest"]:
                if col in row:
                    out.loc[mask, col] = row[col]
            out.loc[mask, "contract"] = row["symbol"]
            out.loc[mask, "main_contract"] = row["symbol"]
            out.loc[mask, "source"] = f"{exchange}_OFFICIAL_EOD"
            out.loc[mask, "source_tier"] = 3
            out.loc[mask, "lineage_status"] = "latest_only"
            out.loc[mask, "open_interest_change"] = np.nan
    return out


def update_daily(start: str = "20200101", offline: bool = False) -> dict:
    ensure_dirs()
    collector = SinaDailyCollector()
    errors = []
    provider_frames = []
    for symbol in SYMBOLS:
        cache = DATA / "raw" / "provider_continuous" / f"{symbol}.parquet"
        try:
            if not offline:
                result = collector.fetch(symbol, start)
                save_result(result, cache)
            raw = pd.read_parquet(cache)
            provider_frames.append(_provider_to_bar(raw))
        except Exception as exc:
            errors.append({"symbol": symbol, "stage": "provider_continuous", "error": repr(exc)})

    def fetch_one(symbol: str, contract: str):
        cache = DATA / "raw" / "contracts" / symbol / f"{contract}.parquet"
        try:
            if not offline and not cache.exists():
                result = SinaDailyCollector().fetch_contract(symbol, contract)
                if not result.frame.empty:
                    save_result(result, cache)
            return symbol, contract, pd.read_parquet(cache) if cache.exists() else None, None
        except Exception as exc:
            message = repr(exc)
            if "Expected axis has 0 elements" in message:
                return symbol, contract, None, None
            return symbol, contract, None, message

    contract_frames: dict[str, list[pd.DataFrame]] = {symbol: [] for symbol in SYMBOLS}
    jobs = [(symbol, contract) for symbol in SYMBOLS for contract in contract_universe(symbol, max(int(start[:4]) - 1, 2000))]
    workers = 1 if offline else 4
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [executor.submit(fetch_one, symbol, contract) for symbol, contract in jobs]
        for future in as_completed(futures):
            symbol, contract, contract_frame, error = future.result()
            if contract_frame is not None and not contract_frame.empty:
                contract_frames[symbol].append(contract_frame)
            elif error:
                errors.append({"symbol": symbol, "contract": contract, "stage": "contract_history", "error": error})

    governed_frames, term_frames, governed_symbols = [], [], []
    for symbol, frames in contract_frames.items():
        if not frames:
            continue
        panel = pd.concat(frames, ignore_index=True)
        panel = panel[pd.to_datetime(panel["trade_date"]) >= pd.Timestamp(start)]
        if panel.empty:
            continue
        governed = _clean_bars(build_main_continuous(panel))
        governed["research_eligible"] = True
        governed_frames.append(governed)
        governed_symbols.append(symbol)
        structure = build_term_structure(panel)
        if not structure.empty:
            term_frames.append(structure)
    if not governed_frames:
        raise RuntimeError("No single-contract history is available; cannot create governed research series")
    governed_all = pd.concat(governed_frames, ignore_index=True)
    term = pd.concat(term_frames, ignore_index=True) if term_frames else pd.DataFrame()
    fallback_frames = [x for x in provider_frames if not x.empty and x["symbol"].iloc[0] not in governed_symbols]
    other = pd.concat(fallback_frames, ignore_index=True) if fallback_frames else pd.DataFrame()
    if not other.empty:
        other = _overlay_cached_official_latest(other)
    datasets = [governed_all] + ([] if other.empty else [other])
    common = sorted(set().union(*(set(data.columns) for data in datasets)))
    for data in datasets:
        for col in common:
            if col not in data:
                data[col] = pd.NA
    bars = _clean_bars(pd.concat([data[common] for data in datasets], ignore_index=True).sort_values(["trade_date", "symbol"]))
    bars.to_parquet(DATA / "daily" / "daily_bars.parquet", index=False)
    term.to_parquet(DATA / "daily" / "term_structure.parquet", index=False)
    features = calculate_features(governed_all, term)
    features.to_parquet(DATA / "feature_store" / "features_daily.parquet", index=False)
    quality = run_quality_checks(bars, features)
    quality.to_csv(REPORTS / "data_quality" / "latest.csv", index=False, encoding="utf-8-sig")
    db = Database()
    try:
        db.replace_frame("daily_bars", bars)
        db.replace_frame("term_structure", term)
        db.replace_frame("features_daily", features)
        db.replace_frame("data_quality", quality)
    finally:
        db.close()
    error_path = REPORTS / "data_quality" / "api_errors.json"
    if not offline or not error_path.exists():
        error_path.write_text(json.dumps(errors, ensure_ascii=False, indent=2), encoding="utf-8")
    result = {"finished_at": datetime.now(timezone.utc).isoformat(), "bars": len(bars), "research_rows": len(features),
              "symbols": sorted(bars.symbol.unique().tolist()), "research_symbols": sorted(governed_symbols),
              "governed_rolls": int(governed_all.roll_flag.sum()), "api_errors": len(errors)}
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="20200101")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    print(json.dumps(update_daily(args.start, args.offline), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
