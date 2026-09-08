from __future__ import annotations

import akshare as ak
import pandas as pd

from collectors.base import CollectorResult, MarketDataCollector


class ExchangeDailyCollector(MarketDataCollector):
    """Tier-3 official exchange EOD adapter. Failures are surfaced, never hidden."""

    source_tier = 3

    def __init__(self, exchange: str):
        self.exchange = exchange

    def fetch(self, symbol: str, start: str, end: str | None = None) -> CollectorResult:
        raw = ak.get_futures_daily(start_date=start, end_date=end or start, market=self.exchange)
        if raw.empty:
            raise RuntimeError(f"Official {self.exchange} returned no rows for {start}..{end or start}")
        raw.columns = [str(c).lower() for c in raw.columns]
        return CollectorResult(raw, f"{self.exchange}_OFFICIAL_EOD", 3, self.now_utc())
