from __future__ import annotations

import pandas as pd


def build_term_structure(contract_panel: pd.DataFrame) -> pd.DataFrame:
    """Select the first two non-expired contracts by maturity for each symbol/date."""
    rows = []
    panel = contract_panel.copy()
    panel["contract_num"] = panel["contract"].str.extract(r"(\d+)$")[0].astype(int)
    for (trade_date, symbol), day in panel.groupby(["trade_date", "symbol"], sort=True):
        liquid = day[(day["volume"] > 0) & day["close"].notna()].sort_values("contract_num")
        if len(liquid) < 2:
            continue
        near, far = liquid.iloc[0], liquid.iloc[1]
        rows.append({
            "trade_date": trade_date, "symbol": symbol,
            "near_contract": near["contract"], "near_price": near["close"],
            "far_contract": far["contract"], "far_price": far["close"],
            "spread": near["close"] - far["close"],
            "roll_yield_user": (far["close"] - near["close"]) / near["close"],
            "roll_yield_research": (near["close"] - far["close"]) / near["close"],
        })
    return pd.DataFrame(rows)
