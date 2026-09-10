import pytest
from pathlib import Path
from streamlit.testing.v1 import AppTest


PAGES = ["市场总览", "生存风险", "持仓结构", "择时状态", "历史相似", "横截面雷达", "数据质量"]


@pytest.mark.parametrize("page", PAGES)
def test_dashboard_page_has_no_exception(page):
    app_path = Path(__file__).resolve().parents[1] / "dashboard" / "app.py"
    app = AppTest.from_file(app_path, default_timeout=30).run()
    app.radio[0].set_value(page).run()
    assert not app.exception


def test_streamlit_entrypoint_renders_for_multiple_sessions(monkeypatch):
    """Guard against importing a cached dashboard module on later sessions."""
    monkeypatch.delenv("DASHBOARD_PASSWORD", raising=False)
    app_path = Path(__file__).resolve().parents[1] / "streamlit_app.py"

    first_session = AppTest.from_file(app_path, default_timeout=30).run()
    second_session = AppTest.from_file(app_path, default_timeout=30).run()

    assert not first_session.exception
    assert not second_session.exception
    assert first_session.radio
    assert second_session.radio
