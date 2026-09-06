import pandas as pd
import pytest

from features.microstructure import calculate_microstructure


def test_simulated_data_cannot_create_ofi():
    ticks = pd.DataFrame({"event_time": ["2024-01-01"], "bid": [1], "ask": [2], "bid_size": [1], "ask_size": [1], "last_price": [1.5], "volume": [1], "is_simulated": [True]})
    with pytest.raises(ValueError, match="real tick"):
        calculate_microstructure(ticks)
