from __future__ import annotations

import argparse
import json

from backtest.report import run_backtests
from scheduler.daily_report import generate_daily_report
from scheduler.update_daily import update_daily
from scheduler.update_intraday import simulate_ticks


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="20200101")
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()
    daily = update_daily(args.start, args.offline)
    backtest = run_backtests()
    json_path, md_path = generate_daily_report()
    print(json.dumps({"daily": daily, "backtest": backtest, "report_json": str(json_path), "report_md": str(md_path),
                      "simulated_stream_smoke_rows": len(simulate_ticks(ticks=10))}, ensure_ascii=False, indent=2, default=str))


if __name__ == "__main__":
    main()
