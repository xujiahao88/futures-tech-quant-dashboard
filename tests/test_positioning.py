import pandas as pd

from collectors.term_structure import build_term_structure


def test_roll_yield_sign_conventions_are_both_kept():
    panel = pd.DataFrame([
        {"trade_date": "2024-01-01", "symbol": "I", "contract": "I2401", "close": 100.0, "volume": 1},
        {"trade_date": "2024-01-01", "symbol": "I", "contract": "I2405", "close": 110.0, "volume": 1},
    ])
    out = build_term_structure(panel).iloc[0]
    assert out.roll_yield_user == .1
    assert out.roll_yield_research == -.1
