from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
DATA = ROOT / "data"
REPORTS = ROOT / "reports"
DB_PATH = ROOT / os.getenv("DATABASE_PATH", "data/commodity_quant.duckdb")

SYMBOLS = {
    "I": {"name": "铁矿石", "exchange": "DCE", "provider": "I0", "group": "black"},
    "JM": {"name": "焦煤", "exchange": "DCE", "provider": "JM0", "group": "black"},
    "J": {"name": "焦炭", "exchange": "DCE", "provider": "J0", "group": "black"},
    "RB": {"name": "螺纹钢", "exchange": "SHFE", "provider": "RB0", "group": "black"},
    "HC": {"name": "热卷", "exchange": "SHFE", "provider": "HC0", "group": "black"},
    "LC": {"name": "碳酸锂", "exchange": "GFEX", "provider": "LC0", "group": "new_energy"},
    "SI": {"name": "工业硅", "exchange": "GFEX", "provider": "SI0", "group": "new_energy"},
    "PS": {"name": "多晶硅", "exchange": "GFEX", "provider": "PS0", "group": "new_energy"},
}

ROLL_RULE = {
    "primary": "volume",
    "secondary": "open_interest",
    "challenger_ratio": 1.20,
    "confirmation_days": 2,
    "allow_backward_roll": False,
    "adjustment_method": "forward_additive",
    "return_method": "same_contract_close_to_close",
}

EVENT_OFFSETS = [-60, -40, -20, -10, -5, 0, 5, 10, 20, 40]


def ensure_dirs() -> None:
    for relative in [
        "raw/provider_continuous", "raw/contracts", "daily", "minute", "tick",
        "feature_store", "events", "reports", "../reports/backtest",
        "../reports/daily", "../reports/data_quality",
    ]:
        (DATA / relative).resolve().mkdir(parents=True, exist_ok=True)
