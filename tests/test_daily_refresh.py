from datetime import date

import pandas as pd

from scheduler.update_daily import _active_contracts, _merge_contract_history


def test_active_contracts_excludes_expired_delivery_months():
    contracts = _active_contracts("RB", date(2026, 9, 10))

    assert "RB2605" not in contracts
    assert "RB2610" in contracts
    assert "RB2701" in contracts


def test_merge_contract_history_preserves_cache_and_revises_overlap():
    cached = pd.DataFrame({"trade_date": ["2026-09-08", "2026-09-09"], "close": [100.0, 101.0]})
    fresh = pd.DataFrame({"trade_date": ["2026-09-09", "2026-09-10"], "close": [102.0, 103.0]})

    merged = _merge_contract_history(cached, fresh)

    assert merged["trade_date"].dt.strftime("%Y-%m-%d").tolist() == ["2026-09-08", "2026-09-09", "2026-09-10"]
    assert merged["close"].tolist() == [100.0, 102.0, 103.0]
