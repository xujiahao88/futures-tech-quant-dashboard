from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

import pandas as pd


@dataclass(frozen=True)
class CollectorResult:
    frame: pd.DataFrame
    source: str
    source_tier: int
    retrieved_at: str
    is_simulated: bool = False


class MarketDataCollector(ABC):
    source_tier: Literal[1, 2, 3, 4, 5]

    @abstractmethod
    def fetch(self, symbol: str, start: str, end: str | None = None) -> CollectorResult:
        raise NotImplementedError

    @staticmethod
    def now_utc() -> str:
        return datetime.now(timezone.utc).isoformat()
