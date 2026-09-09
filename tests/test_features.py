import numpy as np
import pandas as pd

from features.survival import add_survival_features
from features.timing import hurst_rs, katz_fd


def test_var99_marks_small_sample():
    n = 300
    close = 100 * np.exp(np.cumsum(np.random.default_rng(1).normal(0, .01, n)))
    frame = pd.DataFrame({"trade_date": pd.date_range("2020-01-01", periods=n), "open": close, "high": close*1.01, "low": close*.99, "close": close, "adjusted_close": close, "analysis_return": pd.Series(close).pct_change(), "turnover": np.nan})
    out = add_survival_features(frame)
    assert out.iloc[-1].var99_sample_status == "insufficient_sample"
    assert pd.isna(out.iloc[-1].var99)


def test_algorithm_outputs_are_finite():
    x = np.linspace(1, 2, 120) + np.sin(np.arange(120)) * .01
    assert np.isfinite(hurst_rs(x))
    assert np.isfinite(katz_fd(x))
