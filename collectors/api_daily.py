from __future__ import annotations

from datetime import date
from pathlib import Path

import akshare as ak
import pandas as pd

from collectors.base import CollectorResult, MarketDataCollector
from config import DATA, SYMBOLS


STANDARD_COLUMNS = [
    "trade_date", "symbol", "contract", "open", "high", "low", "close",
    "settlement", "volume", "turnover", "open_interest", "open_interest_change",
    "source", "source_tier", "is_simulated", "lineage_status",
]


def _standardize(df: pd.DataFrame, symbol: str, contract: str, lineage: str) -> pd.DataFrame:
    out = df.rename(columns={"date": "trade_date", "hold": "open_interest", "settle": "settlement"}).copy()
    out["trade_date"] = pd.to_datetime(out["trade_date"])
    out["symbol"] = symbol
    out["contract"] = contract
    out["turnover"] = pd.NA
    out["open_interest_change"] = pd.to_numeric(out["open_interest"], errors="coerce").diff()
    out["source"] = "SINA_PUBLIC_API"
    out["source_tier"] = 4
    out["is_simulated"] = False
    out["lineage_status"] = lineage
    for col in STANDARD_COLUMNS:
        if col not in out:
            out[col] = pd.NA
    return out[STANDARD_COLUMNS].sort_values("trade_date").reset_index(drop=True)


class SinaDailyCollector(MarketDataCollector):
    """Tier-4 public API collector. It is not the production realtime chain."""

    source_tier = 4

    def fetch(self, symbol: str, start: str = "19900101", end: str | None = None) -> CollectorResult:
        provider_symbol = SYMBOLS[symbol]["provider"]
        # This endpoint exposes the stable normalized date/OHLC/volume/OI schema.
        # futures_main_sina has changed column naming across provider releases.
        raw = ak.futures_zh_daily_sina(symbol=provider_symbol)
        if not raw.empty:
            dates = pd.to_datetime(raw["date"])
            raw = raw[(dates >= pd.Timestamp(start)) & (dates <= pd.Timestamp(end or "2222-01-01"))]
        frame = _standardize(raw, symbol, provider_symbol, "provider_unavailable")
        return CollectorResult(frame, "SINA_PUBLIC_API", 4, self.now_utc())

    def fetch_contract(self, symbol: str, contract: str) -> CollectorResult:
        raw = ak.futures_zh_daily_sina(symbol=contract)
        frame = _standardize(raw, symbol, contract, "complete")
        return CollectorResult(frame, "SINA_PUBLIC_API", 4, self.now_utc())


CONTRACT_MONTHS = {
    "I": (1, 5, 9), "J": (1, 5, 9), "JM": (1, 5, 9),
    "RB": (1, 5, 10), "HC": (1, 5, 10),
    "LC": tuple(range(1, 13)), "SI": tuple(range(1, 13)), "PS": tuple(range(1, 13)),
}
LISTING_YEARS = {"I": 2013, "J": 2011, "JM": 2013, "RB": 2009, "HC": 2014, "LC": 2023, "SI": 2022, "PS": 2024}


def contract_universe(symbol: str, start_year: int, end_year: int | None = None) -> list[str]:
    """Auditable contract universe; new-energy products use every delivery month."""
    end_year = end_year or (date.today().year + 1)
    first_year = max(LISTING_YEARS[symbol], start_year)
    return [f"{symbol}{str(y)[-2:]}{m:02d}" for y in range(first_year, end_year + 1) for m in CONTRACT_MONTHS[symbol]]


def iron_ore_contracts(start_year: int = 2019, end_year: int | None = None) -> list[str]:
    """Backward-compatible wrapper."""
    return contract_universe("I", start_year, end_year)


def save_result(result: CollectorResult, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    result.frame.to_parquet(path, index=False)
