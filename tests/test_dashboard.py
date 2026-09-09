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
