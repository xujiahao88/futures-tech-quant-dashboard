from __future__ import annotations

import argparse
import json
from datetime import date

import pandas as pd

from collectors.exchange_daily import ExchangeDailyCollector
from collectors.router import SourceRouter
from config import DATA, REPORTS, ensure_dirs


def probe(trade_date: str) -> dict:
    ensure_dirs()
    result = {"trade_date": trade_date, "capabilities": {}, "official_probes": {}}
    router = SourceRouter()
    for exchange in ("DCE", "SHFE", "GFEX"):
        result["capabilities"][exchange] = router.capabilities(exchange)
        try:
            frame = ExchangeDailyCollector(exchange).fetch("*", trade_date, trade_date).frame
            for column in ["open", "high", "low", "close", "volume", "open_interest", "turnover", "settle", "pre_settle"]:
                if column in frame:
                    frame[column] = pd.to_numeric(frame[column], errors="coerce")
            result["official_probes"][exchange] = {"status": "ok", "rows": len(frame)}
            cache = DATA / "raw" / "official" / f"{exchange}_{trade_date}.parquet"
            cache.parent.mkdir(parents=True, exist_ok=True)
            frame.to_parquet(cache, index=False)
        except Exception as exc:
            result["official_probes"][exchange] = {"status": "error", "error": repr(exc)}
    path = REPORTS / "data_quality" / "source_probe.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=date.today().strftime("%Y%m%d"))
    args = parser.parse_args()
    print(json.dumps(probe(args.date), ensure_ascii=False, indent=2))
