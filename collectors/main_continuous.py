from __future__ import annotations

import re

import numpy as np
import pandas as pd

from config import ROLL_RULE


def _maturity(contract: str) -> int:
    match = re.search(r"(\d{4})$", contract)
    return int(match.group(1)) if match else -1


def build_main_continuous(panel: pd.DataFrame) -> pd.DataFrame:
    """Causal main contract selection with hysteresis and auditable roll lineage."""
    required = {"trade_date", "symbol", "contract", "open", "high", "low", "close", "settlement", "volume", "open_interest"}
    missing = required - set(panel.columns)
    if missing:
        raise ValueError(f"Contract panel missing: {sorted(missing)}")
    panel = panel.copy().sort_values(["trade_date", "contract"])
    panel["trade_date"] = pd.to_datetime(panel["trade_date"])
    output = []
    for symbol, sym_panel in panel.groupby("symbol"):
        current = None
        challenger = None
        streak = 0
        previous_selected = None
        adjustment = 0.0
        by_date = {d: x.set_index("contract") for d, x in sym_panel.groupby("trade_date")}
        dates = sorted(by_date)
        prior_day = None
        for trade_date in dates:
            day = by_date[trade_date]
            eligible = day[(pd.to_numeric(day["volume"], errors="coerce") > 0) & day["close"].notna()]
            if eligible.empty:
                prior_day = trade_date
                continue
            leader = eligible.sort_values(["volume", "open_interest"], ascending=False).index[0]
            if current not in eligible.index:
                chosen = leader
                streak = 0
                challenger = None
            elif leader != current and (ROLL_RULE["allow_backward_roll"] or _maturity(leader) >= _maturity(current)):
                leader_vol = float(eligible.loc[leader, "volume"])
                current_vol = float(eligible.loc[current, "volume"])
                if leader_vol >= current_vol * ROLL_RULE["challenger_ratio"]:
                    if challenger == leader:
                        streak += 1
                    else:
                        challenger, streak = leader, 1
                else:
                    challenger, streak = None, 0
                chosen = leader if streak >= ROLL_RULE["confirmation_days"] else current
            else:
                chosen = current
                challenger, streak = None, 0
            roll_flag = previous_selected is not None and chosen != previous_selected
            selected = eligible.loc[chosen].copy()
            if isinstance(selected, pd.DataFrame):
                selected = selected.iloc[0]
            true_return = np.nan
            if prior_day is not None and chosen in by_date[prior_day].index:
                prior_close = by_date[prior_day].loc[chosen, "close"]
                if isinstance(prior_close, pd.Series):
                    prior_close = prior_close.iloc[0]
                if pd.notna(prior_close) and prior_close != 0:
                    true_return = float(selected["close"]) / float(prior_close) - 1
            if roll_flag and previous_selected in day.index:
                old_close = day.loc[previous_selected, "close"]
                if isinstance(old_close, pd.Series):
                    old_close = old_close.iloc[0]
                adjustment += float(old_close) - float(selected["close"])
            row = selected.to_dict()
            row.update({
                "trade_date": trade_date, "symbol": symbol, "main_contract": chosen,
                "contract": chosen, "roll_flag": bool(roll_flag),
                "previous_contract": previous_selected,
                "next_contract": chosen if roll_flag else None,
                "adjustment_method": ROLL_RULE["adjustment_method"],
                "adjustment_value": adjustment,
                "adjusted_close": float(selected["close"]) + adjustment,
                "true_contract_return": true_return,
                "lineage_status": "complete",
            })
            output.append(row)
            current = chosen
            previous_selected = chosen
            prior_day = trade_date
    out = pd.DataFrame(output).sort_values(["symbol", "trade_date"]).reset_index(drop=True)
    out["analysis_return"] = out.groupby("symbol")["adjusted_close"].pct_change()
    return out
