from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

from config import DATA, ensure_dirs
from database.db import Database


def simulate_ticks(symbol: str = "I", ticks: int = 60, seed: int = 42) -> pd.DataFrame:
    """Operational smoke stream; segregated and forbidden for microstructure research."""
    rng = np.random.default_rng(seed)
    prices = 750 + rng.normal(0, .3, ticks).cumsum()
    now = datetime.now(timezone.utc)
    return pd.DataFrame({
        "event_time": [now + timedelta(seconds=i) for i in range(ticks)], "symbol": symbol,
        "contract": "SIM_I", "bid": prices - .25, "ask": prices + .25,
        "bid_size": rng.integers(10, 100, ticks), "ask_size": rng.integers(10, 100, ticks),
        "last_price": prices, "turnover": np.cumsum(prices * rng.integers(1, 20, ticks)),
        "volume": np.cumsum(rng.integers(1, 20, ticks)), "open_interest": 500000 + rng.integers(-100, 100, ticks).cumsum(),
        "source": "SIMULATED_REALTIME", "is_simulated": True,
    })


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", action="store_true")
    parser.add_argument("--ticks", type=int, default=60)
    args = parser.parse_args()
    if not args.simulate:
        raise SystemExit("No realtime credentials configured. Use --simulate for an explicitly segregated smoke stream.")
    ensure_dirs()
    frame = simulate_ticks(ticks=args.ticks)
    path = DATA / "tick" / "simulated_realtime.parquet"
    frame.to_parquet(path, index=False)
    db = Database()
    try:
        db.replace_frame("simulated_realtime_ticks", frame)
    finally:
        db.close()
    print(json.dumps({"rows": len(frame), "path": str(path), "is_simulated": True}, ensure_ascii=False))


if __name__ == "__main__":
    main()
