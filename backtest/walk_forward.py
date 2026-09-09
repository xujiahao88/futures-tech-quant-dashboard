from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from backtest.event_study import label_events


BASELINE = ["price_pct_120", "momentum20", "rv20", "oi_change_pct"]
INCREMENTAL = ["cvar95", "skew60", "kurtosis60", "roll_yield_research", "top20_net_ratio", "amihud", "hurst_rs_120", "fractal_katz_120"]


def walk_forward_logistic(frame: pd.DataFrame, min_train_days: int = 756, test_days: int = 126) -> pd.DataFrame:
    labeled = label_events(frame).copy()
    dates = sorted(labeled["trade_date"].unique())
    data = labeled.copy()
    data["target_top"] = (data["event_type"] == "TOP").astype(int)
    data = data[data["price_pct_120"] >= .9].sort_values("trade_date")
    features = [f for f in BASELINE + INCREMENTAL if f in data and data[f].notna().mean() >= .15]
    rows = []
    for cutoff in range(min_train_days, len(dates), test_days):
        train_dates, test_dates = dates[:cutoff], dates[cutoff:cutoff + test_days]
        train, test = data[data["trade_date"].isin(train_dates)], data[data["trade_date"].isin(test_dates)]
        if train["target_top"].nunique() < 2 or test.empty:
            continue
        for model_name, cols in [("baseline", [f for f in BASELINE if f in features]), ("incremental", features)]:
            if not cols:
                continue
            model = make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), LogisticRegression(max_iter=1000, class_weight="balanced"))
            model.fit(train[cols], train["target_top"])
            prob = model.predict_proba(test[cols])[:, 1]
            y = test["target_top"].to_numpy()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                auc = roc_auc_score(y, prob) if len(np.unique(y)) > 1 else np.nan
            rows.append({"model": model_name, "train_start": train_dates[0], "train_end": train_dates[-1],
                         "test_start": test_dates[0], "test_end": test_dates[-1], "n_train": len(train), "n_test": len(test),
                         "features": ",".join(cols), "auc": auc, "brier_score": brier_score_loss(y, prob),
                         "log_loss": log_loss(y, prob, labels=[0, 1]),
                         "auc_status": "ok" if len(np.unique(y)) > 1 else "insufficient_test_classes",
                         "test_positive_count": int(y.sum()), "evidence_type": "local_evidence"})
    return pd.DataFrame(rows)
