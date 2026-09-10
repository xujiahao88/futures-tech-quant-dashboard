import pandas as pd

from dashboard.explanations import (
    analog_readout,
    board_readout,
    positioning_readout,
    state_explanation,
    survival_readout,
)


SYMBOL_META = {
    "RB": {"name": "螺纹钢"},
    "LC": {"name": "碳酸锂"},
}


def test_board_readout_uses_calculated_values_and_changes():
    latest = pd.DataFrame(
        [
            {"symbol": "RB", "market_state": "HEALTHY_TREND", "state_change": "UNCHANGED", "momentum20": 0.03, "cvar95": -0.02},
            {"symbol": "LC", "market_state": "NEW_SHORT_TREND", "state_change": "TRANSITION -> NEW_SHORT_TREND", "momentum20": -0.08, "cvar95": -0.09},
        ]
    )

    result = board_readout(latest, SYMBOL_META, business_lag=0, warn_count=3)

    assert "螺纹钢（RB）" in result["facts"][0]
    assert "碳酸锂（LC）" in result["facts"][0]
    assert "TRANSITION -> NEW_SHORT_TREND" in result["changes"]
    assert "3 项质量提醒" in result["risk"]


def test_plain_explanations_include_limits_not_trade_instructions():
    row = pd.Series(
        {
            "price_oi_quadrant": "PRICE_DOWN_OI_UP",
            "roll_yield_research": -0.02,
            "rv20": 0.30,
            "rv60": 0.15,
            "cvar95": -0.05,
        }
    )
    history = pd.DataFrame({"cvar95": [-0.01, -0.02, -0.05]})

    assert "仍需" in positioning_readout(row)
    assert "不应单独" in positioning_readout(row)
    assert "不回答" in survival_readout(row, history)
    assert "不是底部确认" in state_explanation("POTENTIAL_BOTTOM")


def test_analog_readout_states_that_history_is_not_a_prediction():
    analogs = pd.DataFrame(
        {
            "future_return_20d": [0.10, -0.04, 0.02],
            "future_max_drawdown": [-0.03, -0.11, -0.02],
        }
    )

    text = analog_readout(analogs)

    assert "67%" in text
    assert "不是当前行情的概率预测" in text

