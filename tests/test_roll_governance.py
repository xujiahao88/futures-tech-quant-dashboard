import pandas as pd

from collectors.main_continuous import build_main_continuous


def test_roll_return_uses_incoming_contract_previous_close():
    rows = []
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    for i, d in enumerate(dates):
        rows += [
            {"trade_date": d, "symbol": "I", "contract": "I2401", "open": 100+i, "high": 102+i, "low": 99+i, "close": 100+i, "settlement": 100+i, "volume": [1000, 900, 100, 50][i], "open_interest": 1000},
            {"trade_date": d, "symbol": "I", "contract": "I2405", "open": 120+i, "high": 122+i, "low": 119+i, "close": 120+i, "settlement": 120+i, "volume": [100, 1200, 1300, 1400][i], "open_interest": 1200},
        ]
    out = build_main_continuous(pd.DataFrame(rows))
    roll = out[out.roll_flag].iloc[0]
    assert roll.contract == "I2405"
    assert abs(roll.true_contract_return - (122 / 121 - 1)) < 1e-12
    assert abs(roll.analysis_return) < .02


def test_roll_lineage_is_preserved():
    base = pd.DataFrame([
        {"trade_date": "2024-01-01", "symbol": "I", "contract": "I2401", "open": 100, "high": 101, "low": 99, "close": 100, "settlement": 100, "volume": 100, "open_interest": 100},
        {"trade_date": "2024-01-02", "symbol": "I", "contract": "I2401", "open": 100, "high": 101, "low": 99, "close": 100, "settlement": 100, "volume": 100, "open_interest": 100},
    ])
    out = build_main_continuous(base)
    assert {"main_contract", "roll_flag", "previous_contract", "next_contract", "adjustment_method"} <= set(out)
