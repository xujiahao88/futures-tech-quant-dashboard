from __future__ import annotations

import hmac
import html
import os
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtest.analog_search import find_analogs
from config import DATA, REPORTS, SYMBOLS
from dashboard.explanations import (
    PAGE_GUIDES,
    analog_readout,
    board_readout,
    positioning_readout,
    state_explanation,
    survival_readout,
    symbol_plain_readout,
    timing_readout,
)

st.set_page_config(page_title="Commodity Quant Lab", page_icon="◈", layout="wide", initial_sidebar_state="auto")

COLORS = {"ink": "#0B1739", "blue": "#2864DC", "cyan": "#00A7B5", "green": "#12A36D", "red": "#E45757", "amber": "#E99A2B"}
STATE_COLORS = {
    "HEALTHY_TREND": "#12A36D", "HIGH_FRAGILITY": "#E45757", "SHORT_SQUEEZE": "#8B5CF6",
    "LONG_LIQUIDATION": "#D92D20", "NEW_SHORT_TREND": "#F79009", "POTENTIAL_BOTTOM": "#00A7B5",
    "HIGH_NOISE": "#667085", "TRANSITION": "#2864DC", "DATA_LIMITED": "#98A2B3",
}
STATE_LABELS = {
    "HEALTHY_TREND": "健康趋势", "HIGH_FRAGILITY": "高位脆弱", "SHORT_SQUEEZE": "空头挤压",
    "LONG_LIQUIDATION": "多头踩踏", "NEW_SHORT_TREND": "新空趋势", "POTENTIAL_BOTTOM": "潜在底部",
    "HIGH_NOISE": "高噪声", "TRANSITION": "状态过渡", "DATA_LIMITED": "数据受限", "UNCHANGED": "未变化",
}
PAGES = ["市场总览", "生存风险", "持仓结构", "择时状态", "历史相似", "横截面雷达", "数据质量"]

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;600;700&display=swap');
:root { --ink:#0B1739; --muted:#667085; --blue:#2864DC; --line:#E5EAF2; }
html, body, [class*="css"] { font-family:Inter,"Noto Sans SC","Microsoft YaHei",sans-serif; }
.stApp { background:linear-gradient(180deg,#F8FAFD 0,#FFFFFF 330px); color:var(--ink); }
[data-testid="stHeader"] { background:rgba(248,250,253,.86); backdrop-filter:blur(12px); }
[data-testid="stSidebar"] { background:#0B1739; border-right:0; }
[data-testid="stSidebar"] * { color:#EAF0FF; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { padding:.42rem .55rem; border-radius:9px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background:rgba(255,255,255,.08); }
[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div { background:#16264B; border-color:#33456F; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] div[data-baseweb="select"] * { color:#F8FAFF !important; opacity:1 !important; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"] { background:#16264B !important; border-color:#33456F !important; color:#F8FAFF !important; -webkit-text-fill-color:#F8FAFF !important; opacity:1 !important; }
[data-testid="stSidebar"] [data-testid="stSelectbox"] [role="combobox"] * { color:#F8FAFF !important; fill:#F8FAFF !important; -webkit-text-fill-color:#F8FAFF !important; opacity:1 !important; }
.block-container { padding-top:1.45rem; padding-bottom:3rem; max-width:1500px; }
.hero { background:linear-gradient(118deg,#0B1739 0%,#15386F 62%,#087E8B 100%); border-radius:22px; padding:28px 32px; color:white; box-shadow:0 18px 45px rgba(11,23,57,.18); margin-bottom:18px; position:relative; overflow:hidden; }
.hero:after { content:""; position:absolute; width:280px; height:280px; border-radius:50%; right:-70px; top:-120px; border:52px solid rgba(255,255,255,.07); }
.eyebrow { font-size:.72rem; letter-spacing:.16em; text-transform:uppercase; opacity:.72; font-weight:600; }
.hero h1 { color:white; margin:.35rem 0 .3rem; font-size:2rem; letter-spacing:-.03em; }
.hero p { margin:0; color:#D8E5FF; font-size:.94rem; max-width:780px; }
.hero-badge { display:inline-block; margin-top:14px; padding:5px 10px; border:1px solid rgba(255,255,255,.22); border-radius:999px; color:#DDFBFF; font-size:.76rem; background:rgba(255,255,255,.08); }
.metric-card { background:#FFF; border:1px solid #E7EBF2; border-radius:16px; padding:16px 18px; box-shadow:0 8px 24px rgba(17,38,82,.055); min-height:112px; }
.metric-label { color:#667085; font-size:.76rem; font-weight:600; letter-spacing:.04em; text-transform:uppercase; }
.metric-value { color:#0B1739; font-size:1.55rem; font-weight:700; margin-top:9px; letter-spacing:-.03em; }
.metric-note { color:#98A2B3; font-size:.72rem; margin-top:3px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.section-title { font-size:1.05rem; font-weight:700; color:#0B1739; margin:1.2rem 0 .5rem; }
.section-note { color:#667085; font-size:.82rem; margin-bottom:.8rem; }
.state-pill { display:inline-block; color:white; border-radius:999px; padding:5px 11px; font-weight:700; font-size:.72rem; letter-spacing:.03em; }
.coverage { padding:12px 15px; border-radius:12px; background:#EFF8FF; border-left:4px solid #2864DC; color:#344054; font-size:.84rem; margin:.5rem 0 1rem; }
.warning-box { padding:14px 16px; border-radius:12px; background:#FFF8EB; border:1px solid #FDE3AD; color:#7A4D08; font-size:.84rem; }
.insight-card { background:linear-gradient(135deg,#F0F6FF 0%,#F4FBFA 100%); border:1px solid #D7E5FA; border-radius:18px; padding:19px 21px; margin:.65rem 0 1rem; color:#243B64; box-shadow:0 8px 22px rgba(40,100,220,.055); }
.insight-card h3 { color:#0B1739; font-size:1rem; margin:0 0 .45rem; }
.insight-card p { margin:.28rem 0; font-size:.88rem; line-height:1.72; }
.insight-label { display:inline-block; color:#2864DC; background:#E5EEFF; border-radius:999px; padding:3px 8px; margin-right:7px; font-size:.69rem; font-weight:700; letter-spacing:.04em; }
.plain-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:10px; margin:.55rem 0 1rem; }
.plain-item { background:#FFF; border:1px solid #E7EBF2; border-radius:13px; padding:12px 14px; color:#475467; font-size:.81rem; line-height:1.58; }
.plain-item b { color:#0B1739; }
.symbol-note { color:#344054; background:#FAFBFD; border-left:3px solid #7FA7F5; padding:9px 12px; border-radius:8px; font-size:.79rem; line-height:1.55; }
.footer { color:#98A2B3; font-size:.72rem; text-align:center; margin-top:2.5rem; padding-top:1rem; border-top:1px solid #EEF1F6; }
[data-testid="stDataFrame"] { border:1px solid #E7EBF2; border-radius:14px; overflow:hidden; }
[data-testid="stPlotlyChart"] { background:white; border:1px solid #E7EBF2; border-radius:16px; padding:7px; box-shadow:0 6px 18px rgba(17,38,82,.04); }
.hero-badge.stale { background:rgba(228,87,87,.24); border-color:rgba(255,210,210,.52); color:#FFF1F1; }
@media (max-width: 768px) {
  .block-container { padding:1rem .75rem 2rem; }
  .hero { border-radius:16px; padding:31px 19px 22px; }
  .hero .eyebrow { display:none; }
  .hero h1 { font-size:1.62rem; }
  .hero p { font-size:.84rem; line-height:1.65; }
  .metric-card { min-height:96px; padding:13px 14px; }
  .metric-value { font-size:1.3rem; }
  .plain-grid { grid-template-columns:1fr; }
  .insight-card { padding:16px 17px; }
  [data-testid="stDataFrame"] { font-size:.78rem; }
}
</style>
""", unsafe_allow_html=True,
)


def require_password():
    expected = os.getenv("DASHBOARD_PASSWORD", "")
    if not expected:
        return
    if st.session_state.get("authenticated"):
        return
    st.markdown('<div class="hero"><div class="eyebrow">SECURE ACCESS</div><h1>Commodity Quant Lab</h1><p>请输入看板访问密码。</p></div>', unsafe_allow_html=True)
    entered = st.text_input("访问密码", type="password")
    if st.button("进入看板", type="primary", width="stretch"):
        if hmac.compare_digest(entered, expected):
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("密码不正确")
    st.stop()


require_password()


@st.cache_data(ttl=60)
def load_data():
    bars = pd.read_parquet(DATA / "daily" / "daily_bars.parquet")
    features = pd.read_parquet(DATA / "feature_store" / "features_daily.parquet")
    quality = pd.read_csv(REPORTS / "data_quality" / "latest.csv")
    events_path = REPORTS / "backtest" / "events.csv"
    events = pd.read_csv(events_path) if events_path.exists() else pd.DataFrame()
    for frame in (bars, features):
        frame["trade_date"] = pd.to_datetime(frame["trade_date"])
    return bars, features, quality, events


def fmt(value, digits=2, suffix=""):
    return "—" if value is None or pd.isna(value) else f"{float(value):,.{digits}f}{suffix}"


def pct(value, digits=1):
    return "—" if value is None or pd.isna(value) else f"{float(value) * 100:.{digits}f}%"


def metric_card(label, value, note=""):
    st.markdown(f'<div class="metric-card"><div class="metric-label">{label}</div><div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>', unsafe_allow_html=True)


def insight_card(title, paragraphs, label="通俗解读"):
    body = "".join(f"<p>{html.escape(str(paragraph))}</p>" for paragraph in paragraphs if paragraph)
    st.markdown(
        f'<div class="insight-card"><h3><span class="insight-label">{html.escape(label)}</span>{html.escape(title)}</h3>{body}</div>',
        unsafe_allow_html=True,
    )


def beginner_guide(page_name):
    items = PAGE_GUIDES.get(page_name, [])
    if not items:
        return
    cards = "".join(
        f'<div class="plain-item"><b>{html.escape(title)}</b><br>{html.escape(text)}</div>'
        for title, text in items
    )
    st.markdown(f'<div class="plain-grid">{cards}</div>', unsafe_allow_html=True)


def section(title, note=""):
    st.markdown(f'<div class="section-title">{title}</div><div class="section-note">{note}</div>', unsafe_allow_html=True)


def state_pill(state):
    color = STATE_COLORS.get(state, STATE_COLORS["DATA_LIMITED"])
    return f'<span class="state-pill" style="background:{color}">{STATE_LABELS.get(state, state)} · {state}</span>'


def state_display(state):
    state = "DATA_LIMITED" if state is None or pd.isna(state) else str(state)
    return f"{STATE_LABELS.get(state, state)} · {state}"


def state_change_display(change):
    if change is None or pd.isna(change):
        return "—"
    change = str(change)
    if change == "UNCHANGED":
        return "未变化 · UNCHANGED"
    if " -> " in change:
        before, after = change.split(" -> ", 1)
        return f"{STATE_LABELS.get(before, before)} → {STATE_LABELS.get(after, after)} · {change}"
    return change


def style_figure(fig, height=390):
    title_text = fig.layout.title.text if fig.layout.title and fig.layout.title.text not in (None, "undefined") else ""
    fig.update_layout(template="plotly_white", title=dict(text=title_text), height=height, margin=dict(l=18, r=18, t=52, b=22), paper_bgcolor="rgba(0,0,0,0)",
                      plot_bgcolor="#FFFFFF", font=dict(family="Inter, Microsoft YaHei", color="#344054", size=12),
                      title_font=dict(size=15, color="#0B1739"), legend=dict(orientation="h", y=1.08, x=0),
                      hoverlabel=dict(bgcolor="#0B1739", font_color="white"))
    fig.update_xaxes(showgrid=False, linecolor="#E8ECF3")
    fig.update_yaxes(gridcolor="#EEF1F6", zerolinecolor="#D9DEE8")
    return fig


try:
    bars, features, quality, events = load_data()
except FileNotFoundError:
    st.error("尚无运行产物。请先执行 `python -m scheduler.bootstrap`。")
    st.stop()

latest_date = bars["trade_date"].max()
shanghai_today = pd.Timestamp(datetime.now(ZoneInfo("Asia/Shanghai")).date())
business_lag = int(np.busday_count(
    (latest_date.normalize() + pd.Timedelta(days=1)).date(),
    (shanghai_today + pd.Timedelta(days=1)).date(),
)) if latest_date.normalize() < shanghai_today else 0
is_stale = business_lag > 1
latest_bars = bars.sort_values("trade_date").groupby("symbol").tail(1)
latest_features = features.sort_values("trade_date").groupby("symbol").tail(1)
research_symbols = sorted(latest_features["symbol"].unique().tolist())

with st.sidebar:
    st.markdown("## ◈ Commodity Lab")
    st.caption("QUANT RESEARCH CONSOLE")
    page = st.radio("页面导航", PAGES, label_visibility="collapsed")
    st.markdown("---")
    symbol = st.selectbox("研究品种", list(SYMBOLS), format_func=lambda s: f"{s} · {SYMBOLS[s]['name']}")
    beginner_mode = st.toggle("新手解读模式", value=True, help="在指标附近显示通俗解释、当前读法和使用限制。")
    st.caption(f"数据截止 · {latest_date:%Y-%m-%d}")
    st.caption(f"研究覆盖 · {len(research_symbols)}/{len(SYMBOLS)}")
    st.markdown("---")
    st.caption("状态是研究分类，不是交易指令。")

freshness_text = f"滞后 {business_lag} 个工作日" if is_stale else "数据时效正常"
freshness_class = "hero-badge stale" if is_stale else "hero-badge"
st.markdown(f'<div class="hero"><div class="eyebrow">Commodity Quant Agent · Daily Research</div><h1>{page}</h1>'
            f'<p>黑色与新能源商品的量价、尾部风险、持仓结构与历史状态研究。所有统计来自确定性引擎。</p>'
            f'<span class="{freshness_class}">DATA CUT · {latest_date:%Y-%m-%d} · {freshness_text}</span></div>', unsafe_allow_html=True)

sym = features[features.symbol == symbol].sort_values("trade_date")
latest_sym = sym.iloc[-1] if not sym.empty else None
bar_sym = bars[bars.symbol == symbol].sort_values("trade_date")

if page == "市场总览":
    cols = st.columns(4)
    with cols[0]: metric_card("行情覆盖", f"{len(latest_bars)}/8", "8 个目标品种")
    with cols[1]: metric_card("完整研究覆盖", f"{len(research_symbols)}/8", "合约血缘合格")
    with cols[2]: metric_card("最新交易日", f"{latest_date:%m-%d}", f"{latest_date:%Y}")
    with cols[3]: metric_card("质量提醒", str(int((quality.severity == "WARN").sum())), "WARN · 不含硬错误")
    summary_frame = latest_bars[["symbol", "contract", "close", "source", "research_eligible"]].merge(
        latest_features, on="symbol", how="left", suffixes=("_bar", "")
    )
    if beginner_mode:
        reading = board_readout(
            summary_frame,
            SYMBOLS,
            business_lag,
            int((quality.severity == "WARN").sum()),
        )
        insight_card(
            "今天的市场，用一分钟看懂",
            [reading["headline"], *reading["facts"], reading["changes"], reading["risk"]],
            "今日归纳",
        )
    section("市场状态矩阵", "空值代表没有合格数据，不代表风险为零。")
    overview = latest_bars[["symbol", "contract", "close", "source", "research_eligible"]].merge(
        latest_features[["symbol", "market_state", "state_change", "momentum20", "rv20", "cvar95", "oi_change_pct"]], on="symbol", how="left")
    overview["品种"] = overview.symbol.map(lambda x: f"{x} · {SYMBOLS[x]['name']}")
    overview["状态"] = overview.market_state.map(state_display)
    overview["状态变化"] = overview.state_change.map(state_change_display)
    overview["20日动量"] = overview.momentum20.map(pct); overview["RV20"] = overview.rv20.map(pct)
    overview["CVaR95"] = overview.cvar95.map(pct); overview["OI变化"] = overview.oi_change_pct.map(pct)
    overview["研究覆盖"] = np.where(overview.research_eligible.fillna(False), "完整", "价格事实")
    if beginner_mode:
        overview["通俗解读"] = overview.apply(
            lambda row: symbol_plain_readout(row, f"{SYMBOLS[row.symbol]['name']}："), axis=1
        )
    overview_columns = ["品种", "contract", "close", "状态", "状态变化", "20日动量", "RV20", "CVaR95", "OI变化", "研究覆盖", "source"]
    if beginner_mode:
        overview_columns.insert(5, "通俗解读")
    st.dataframe(overview[overview_columns]
                 .rename(columns={"contract": "主力合约", "close": "收盘", "source": "来源"}), width="stretch", hide_index=True, height=360)
    if beginner_mode:
        with st.expander("这些市场状态分别是什么意思？"):
            for state in overview["market_state"].dropna().drop_duplicates():
                st.markdown(f"**{state_display(state)}**")
                st.caption(state_explanation(state))
    section("归一化价格走势", "近约 252 个交易日以各自首日为 100，便于比较相对表现。")
    recent = bars[bars.trade_date >= latest_date - pd.Timedelta(days=390)][["trade_date", "symbol", "close"]].copy()
    recent["价格指数"] = recent.groupby("symbol")["close"].transform(lambda s: s / s.iloc[0] * 100)
    fig = px.line(recent, x="trade_date", y="价格指数", color="symbol", color_discrete_sequence=px.colors.qualitative.Safe)
    st.plotly_chart(style_figure(fig, 430), width="stretch")

elif page == "生存风险":
    if latest_sym is None:
        st.markdown('<div class="warning-box">该品种尚未完成可审计主力拼接，尾部风险指标保持禁用。</div>', unsafe_allow_html=True)
    else:
        cols = st.columns(5)
        values = [("RV20", pct(latest_sym.get("rv20")), "年化实现波动"), ("VaR 95", pct(latest_sym.get("var95")), "历史模拟左尾"),
                  ("CVaR 95", pct(latest_sym.get("cvar95")), "尾部平均损失"), ("最大回撤", pct(latest_sym.get("max_drawdown_250")), "滚动 250 日"),
                  ("回撤时长", fmt(latest_sym.get("drawdown_duration"), 0, " 日"), "当前水下期")]
        for col, item in zip(cols, values):
            with col: metric_card(*item)
        if beginner_mode:
            insight_card(
                f"{SYMBOLS[symbol]['name']}的风险怎么读",
                [survival_readout(latest_sym, sym)],
            )
            beginner_guide("生存风险")
        section(f"{symbol} 波动率与尾部风险", "99% 指标不足 500 个有效样本时显示为空。")
        left, right = st.columns([1.25, 1])
        with left:
            st.plotly_chart(style_figure(px.line(sym, x="trade_date", y=["rv5", "rv20", "rv60"], labels={"value": "年化波动率", "variable": "窗口"})), width="stretch")
        with right:
            st.plotly_chart(style_figure(px.line(sym, x="trade_date", y=["var95", "cvar95", "var99", "cvar99"], labels={"value": "收益率", "variable": "尾部指标"})), width="stretch")
        section("分布形态与流动性", "峰度、偏度不能单独解释为方向信号；没有真实成交额时 Amihud 保持缺失。")
        st.dataframe(sym.tail(30)[["trade_date", "skew60", "kurtosis60", "drawdown", "drawdown_duration", "amihud", "amihud_status", "var99_sample_status"]], width="stretch", hide_index=True)

elif page == "持仓结构":
    if latest_sym is None:
        st.markdown('<div class="warning-box">该品种尚未完成单合约治理，持仓结构研究暂不可用。</div>', unsafe_allow_html=True)
    else:
        cols = st.columns(5)
        items = [("主力合约", str(latest_sym.get("contract", "—")), "血缘可审计"), ("持仓量", fmt(latest_sym.get("open_interest"), 0), "OI level"),
                 ("OI 日变化", pct(latest_sym.get("oi_change_pct")), str(latest_sym.get("price_oi_quadrant", ""))),
                 ("成交/OI", fmt(latest_sym.get("volume_oi"), 2), "换手强度"), ("研究 Roll Yield", pct(latest_sym.get("roll_yield_research")), "(near-far)/near")]
        for col, item in zip(cols, items):
            with col: metric_card(*item)
        if beginner_mode:
            insight_card(
                f"{SYMBOLS[symbol]['name']}的价仓关系怎么读",
                [positioning_readout(latest_sym)],
            )
            beginner_guide("持仓结构")
        section(f"{symbol} 价格 × 持仓", "价格使用防换月跳空连续价；持仓量为当日实际主力合约。")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=sym.trade_date, y=sym.adjusted_close, name="连续价格", line=dict(color=COLORS["blue"], width=2.2)))
        fig.add_trace(go.Scatter(x=sym.trade_date, y=sym.open_interest, name="持仓量", yaxis="y2", line=dict(color=COLORS["amber"], width=1.6)))
        fig.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False, title="OI"))
        st.plotly_chart(style_figure(fig, 430), width="stretch")
        left, right = st.columns(2)
        with left:
            st.plotly_chart(style_figure(px.line(sym, x="trade_date", y=["roll_yield_user", "roll_yield_research"], labels={"value": "Roll Yield", "variable": "口径"}), 350), width="stretch")
        with right:
            st.markdown('<div class="coverage"><b>Basis Momentum</b><br>当前没有治理后的现货 benchmark，因此保持缺失；近远月价差不再冒充基差。</div>', unsafe_allow_html=True)
            st.dataframe(sym.tail(12)[["trade_date", "contract", "roll_flag", "previous_contract", "next_contract", "price_oi_quadrant", "volume_oi"]], width="stretch", hide_index=True)

elif page == "择时状态":
    if latest_sym is None:
        st.markdown('<div class="warning-box">该品种尚无合格择时特征。</div>', unsafe_allow_html=True)
    else:
        state = latest_sym.get("market_state", "TRANSITION")
        st.markdown(state_pill(state), unsafe_allow_html=True)
        st.caption(f"状态变化 · {state_change_display(latest_sym.get('state_change'))}")
        cols = st.columns(5)
        items = [("Momentum 20", pct(latest_sym.get("momentum20")), "20 日动量"), ("价格分位", pct(latest_sym.get("price_pct_120")), "120 日位置"),
                 ("Hurst R/S", fmt(latest_sym.get("hurst_rs_120"), 3), "算法固定 R/S"), ("Katz FD", fmt(latest_sym.get("fractal_katz_120"), 3), "算法固定 Katz"),
                 ("RV 期限结构", fmt(latest_sym.get("rv_term_structure"), 2), "RV5 / RV60")]
        for col, item in zip(cols, items):
            with col: metric_card(*item)
        if beginner_mode:
            insight_card(
                f"{SYMBOLS[symbol]['name']}当前处于什么阶段",
                [timing_readout(latest_sym)],
            )
            beginner_guide("择时状态")
        section(f"{symbol} 趋势骨架", "均线和价格采用连续研究序列；换月跳空不会进入拐点识别。")
        fig = go.Figure()
        for col, color, width in [("adjusted_close", "#0B1739", 2.4), ("ma5", "#00A7B5", 1.3), ("ma20", "#2864DC", 1.5), ("ma60", "#E99A2B", 1.5)]:
            fig.add_trace(go.Scatter(x=sym.trade_date, y=sym[col], name=col.upper(), line=dict(color=color, width=width)))
        st.plotly_chart(style_figure(fig, 450), width="stretch")
        left, right = st.columns(2)
        with left:
            st.plotly_chart(style_figure(px.line(sym, x="trade_date", y=["momentum5", "momentum20", "momentum60"], labels={"value": "动量", "variable": "窗口"}), 340), width="stretch")
        with right:
            st.plotly_chart(style_figure(px.line(sym, x="trade_date", y=["hurst_rs_120", "fractal_katz_120"], labels={"value": "值", "variable": "结构指标"}), 340), width="stretch")
        st.markdown('<div class="coverage"><b>微观结构：</b>无真实分钟/Tick 时，POC、OFI、盘口不平衡和价格冲击继续严格禁用。</div>', unsafe_allow_html=True)

elif page == "历史相似":
    if latest_sym is None:
        st.markdown('<div class="warning-box">该品种尚不可进行历史相似状态搜索。</div>', unsafe_allow_html=True)
    else:
        n = st.slider("返回相似日期", 3, 20, 10)
        analogs = find_analogs(features, symbol, n=n)
        cols = st.columns(3)
        with cols[0]: metric_card("相似样本", str(len(analogs)), "排除近 60 天")
        with cols[1]: metric_card("最佳相似度", fmt(analogs.similarity_score.max() if not analogs.empty else np.nan, 3), "1 / (1 + distance)")
        with cols[2]: metric_card("当前状态", str(latest_sym.get("market_state", "—")), "仅作状态分类")
        if beginner_mode:
            insight_card("相似历史告诉了我们什么", [analog_readout(analogs)])
            beginner_guide("历史相似")
        section("最相似历史日期", "未来收益是历史样本真实后验，用于情景参照，不代表当前预测。")
        st.dataframe(analogs.rename(columns={"trade_date": "日期", "market_state": "当时状态", "similarity_score": "相似度", "future_return_5d": "未来5日",
                                                      "future_return_20d": "未来20日", "future_return_40d": "未来40日", "future_max_drawdown": "未来最大回撤",
                                                      "future_max_rebound": "未来最大反弹", "event_type": "事件类型"}), width="stretch", hide_index=True)
        if not events.empty:
            section("事件对照组", "同时保留高位反转与高位继续、底部反转与低位继续。")
            counts = events[events.symbol == symbol]["event_type"].value_counts().rename_axis("事件").reset_index(name="样本数")
            fig = px.bar(counts, x="事件", y="样本数", color="事件", color_discrete_map={"TOP": "#E45757", "HIGH_CONTINUE": "#2864DC", "BOTTOM": "#12A36D", "LOW_CONTINUE": "#E99A2B"})
            st.plotly_chart(style_figure(fig, 340), width="stretch")

elif page == "横截面雷达":
    section("黑色与新能源强弱画像", "维度转换为当日品种横截面 0–1 分位；缺失时不伪造分数。")
    if beginner_mode:
        insight_card(
            "雷达图不是综合打分",
            [
                "向外伸得越长，只表示该品种在当天 8 个品种中的相对排名更高。趋势靠外偏强；波动、尾部风险、流动性冲击和拥挤度靠外则意味着风险更高。",
                "因此不能把雷达面积最大的品种理解为“最好”，应逐个维度查看。",
            ],
        )
        beginner_guide("横截面雷达")
    latest = latest_features.copy()
    score_specs = {"趋势": ("momentum20", 1), "持仓": ("oi_percentile_250", 1), "波动": ("rv20", 1), "尾部风险": ("cvar95", -1), "流动性冲击": ("amihud", 1), "拥挤度": ("crowding_percentile", 1)}
    for label, (column, direction) in score_specs.items():
        latest[label] = (latest[column] * direction).rank(pct=True) if column in latest else np.nan
    for group_name, members in [("黑色", ["I", "JM", "J", "RB", "HC"]), ("新能源", ["LC", "SI", "PS"])]:
        subset = latest[latest.symbol.isin(members)]
        st.markdown(f"#### {group_name}")
        if subset.empty:
            st.info("该板块暂无完整研究样本。")
            continue
        fig = go.Figure(); dimensions = list(score_specs)
        for _, row in subset.iterrows():
            values = [row.get(col, np.nan) for col in dimensions]
            display = [0 if pd.isna(v) else float(v) for v in values]
            fig.add_trace(go.Scatterpolar(r=display + display[:1], theta=dimensions + dimensions[:1], fill="toself", name=row.symbol, opacity=.65))
        fig.update_layout(polar=dict(bgcolor="#FBFCFE", radialaxis=dict(visible=True, range=[0, 1], gridcolor="#E7EBF2"), angularaxis=dict(gridcolor="#E7EBF2")))
        st.plotly_chart(style_figure(fig, 410), width="stretch")
    st.caption("雷达中的 0 不代表真实值为零；上游缺失会在数据质量页显示原因。")

elif page == "数据质量":
    severity_counts = quality.severity.value_counts(); cols = st.columns(4)
    with cols[0]: metric_card("检查项", str(len(quality)), "自动质量规则")
    with cols[1]: metric_card("通过", str(int(severity_counts.get("OK", 0))), "OK")
    with cols[2]: metric_card("提醒", str(int(severity_counts.get("WARN", 0))), "WARN")
    with cols[3]: metric_card("错误", str(int(severity_counts.get("ERROR", 0))), "ERROR")
    if beginner_mode:
        errors = int(severity_counts.get("ERROR", 0))
        warns = int(severity_counts.get("WARN", 0))
        conclusion = (
            f"当前有 {errors} 项关键错误，涉及的研究结论应暂停使用。"
            if errors
            else f"当前没有关键错误，有 {warns} 项提醒。提醒通常来自字段缺失、样本不足或清洗记录，页面仍可查看，但要结合具体限制。"
        )
        insight_card("这些质量提示会不会影响阅读", [conclusion, "系统不会把缺失值当成 0，也不会用日线数据伪造分钟或 Tick 指标。"])
        beginner_guide("数据质量")
    section("质量检查明细", "覆盖最新时间、字段缺失、数据源、清洗、合约换月、研究资格和样本不足。")
    if is_stale:
        st.markdown(f'<div class="warning-box"><b>行情时效提醒：</b>最新数据为 {latest_date:%Y-%m-%d}，相对上海当前日期滞后 {business_lag} 个工作日。公开源本次未返回更新记录，请勿将旧数据当作实时行情。</div>', unsafe_allow_html=True)
    severity_filter = st.multiselect("严重程度", ["ERROR", "WARN", "OK"], default=["ERROR", "WARN"])
    filtered = quality[quality.severity.isin(severity_filter)] if severity_filter else quality
    st.dataframe(filtered, width="stretch", hide_index=True, height=510)
    source_probe = REPORTS / "data_quality" / "source_probe.json"
    if source_probe.exists():
        with st.expander("查看数据源健康探测"):
            st.code(source_probe.read_text(encoding="utf-8"), language="json")

st.markdown('<div class="footer">Commodity Quant Agent · 数据事实 / 计算结果 / 研究解释 / 待验证假设</div>', unsafe_allow_html=True)

