from __future__ import annotations

from collectors.api_daily import SinaDailyCollector
from collectors.ctp_feed import CTPFeed
from collectors.exchange_daily import ExchangeDailyCollector
from collectors.realtime_ws import RealtimeWebSocketFeed


class SourceRouter:
    """Explicit source priority: CTP > realtime API > official EOD > public API."""

    def __init__(self):
        self.ctp = CTPFeed()
        self.realtime = RealtimeWebSocketFeed()
        self.public_daily = SinaDailyCollector()

    def capabilities(self, exchange: str) -> list[dict]:
        return [
            {"tier": 1, "source": "CTP", "configured": self.ctp.configured()},
            {"tier": 2, "source": "REALTIME_WS", "configured": self.realtime.configured()},
            {"tier": 3, "source": f"{exchange}_OFFICIAL_EOD", "configured": True,
             "adapter": ExchangeDailyCollector(exchange).__class__.__name__},
            {"tier": 4, "source": "SINA_PUBLIC_API", "configured": True},
            {"tier": 5, "source": "WEB_FALLBACK", "configured": False},
        ]
