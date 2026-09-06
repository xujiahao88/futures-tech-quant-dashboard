from __future__ import annotations

import pandas as pd

from features.cross_section import add_cross_section_features
from features.positioning import add_positioning_features
from features.state import add_states
from features.survival import add_survival_features
from features.timing import add_timing_features


def calculate_features(bars: pd.DataFrame, term_structure: pd.DataFrame | None = None) -> pd.DataFrame:
    frames = []
    for _, group in bars.groupby("symbol", sort=True):
        work = group.copy()
        if term_structure is not None and not term_structure.empty:
            work = work.merge(term_structure, on=["trade_date", "symbol"], how="left")
        work = add_survival_features(work)
        work = add_positioning_features(work)
        work = add_timing_features(work)
        frames.append(work)
    combined = pd.concat(frames, ignore_index=True)
    combined = add_cross_section_features(combined)
    combined = add_states(combined)
    return combined.sort_values(["trade_date", "symbol"]).reset_index(drop=True)
