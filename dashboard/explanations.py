from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd


STATE_EXPLANATIONS = {
    "HEALTHY_TREND": "中期价格仍偏强，均线方向与动量相互确认。它说明趋势结构尚完整，不等于现在适合追涨。",
    "HIGH_FRAGILITY": "价格位于近 120 日高位，涨势仍在，但动量边际减弱且短期波动抬升。可以理解为“位置高、缓冲变薄”。",
    "SHORT_SQUEEZE": "价格较快上涨、持仓减少且收益分布偏向上侧，更像空头减仓推动。它不代表上涨一定持续。",
    "LONG_LIQUIDATION": "价格快速下跌、持仓减少且下侧尾部更重，更像多头集中减仓。它不等同于基本面已经长期转空。",
    "NEW_SHORT_TREND": "价格走弱而总持仓增加，可能有新增空头参与。总持仓无法直接识别多空身份，仍需期限结构和席位数据验证。",
    "POTENTIAL_BOTTOM": "价格处于近 120 日低位，动量仍弱但下跌速度开始放缓。这只是潜在筑底环境，不是底部确认。",
    "HIGH_NOISE": "短期波动明显高于中期，但价格方向不清晰。此时信号容易反复，追涨杀跌的成本通常更高。",
    "TRANSITION": "趋势、波动和持仓尚未形成一致组合，市场处于过渡阶段。等待更多数据通常比强行判断方向更稳妥。",
    "DATA_LIMITED": "关键字段或样本不足，当前只展示可验证的数据事实，不生成完整状态结论。",
}


PAGE_GUIDES = {
    "生存风险": [
        ("RV20", "过去 20 日的实际波动幅度，越高表示价格更容易大起大落；它不表示上涨或下跌方向。"),
        ("VaR 95", "历史上较差 5% 情形的损失分界线。例如 -3% 表示约 5% 的交易日损失超过 3%。"),
        ("CVaR 95", "进入最差 5% 情形后，平均亏损有多大。它比 VaR 更关注极端日的平均伤害。"),
        ("最大回撤", "过去一段时间从高点到低点的最大跌幅，用来描述持有过程中可能经历的压力。"),
        ("偏度 / 峰度", "描述收益分布是否偏向某一侧、极端波动是否更多；不能单独当作看多或看空信号。"),
    ],
    "持仓结构": [
        ("持仓量 OI", "仍未平仓的合约总量。OI 上升说明资金或仓位增加，但无法仅凭它判断新增的是多头还是空头。"),
        ("价格 × OI", "把价格涨跌和总持仓变化放在一起看，用于描述参与度变化，不代表所谓“主力方向”。"),
        ("成交/OI", "当日成交量相对持仓量的比例，可粗略观察换手活跃度；越高不一定越健康。"),
        ("研究 Roll Yield", "按 (近月-远月)/近月 计算。正值表示近月更贵，负值表示远月更贵；两者都不是必涨或必跌。"),
        ("用户 Roll Yield", "按 (远月-近月)/近月 计算，与研究口径符号相反，系统始终分别保存。"),
    ],
    "择时状态": [
        ("Momentum 20", "当前连续价格相对 20 个交易日前的变化，正值偏强、负值偏弱。它描述已经发生的走势。"),
        ("价格分位", "当前价格在近 120 日中的相对位置。90% 表示高于约九成历史观察，不等于已经见顶。"),
        ("Hurst R/S", "用固定 R/S 算法描述序列结构，只适合与同品种、同算法的历史值比较，不能直接给出买卖结论。"),
        ("Katz FD", "用固定 Katz 算法描述路径复杂度。数值变化提示走势形态改变，不代表方向。"),
        ("RV 期限结构", "RV5 / RV60。高于 1 表示近期波动比中期更强，低于 1 表示近期波动相对降温。"),
    ],
    "历史相似": [
        ("相似度", "当前多项标准化特征与历史日期的接近程度。接近不代表之后一定重复。"),
        ("未来收益", "只是在那个历史日期之后真实发生的结果，用来展示可能路径，不是当前预测值。"),
        ("最大回撤 / 反弹", "相似历史窗口内最不利和最有利的路径，帮助同时看到风险与机会。"),
        ("事件对照", "同时保留反转与继续上涨/下跌的样本，避免只挑选成功顶部或底部。"),
    ],
    "横截面雷达": [
        ("雷达分数", "是同一天 8 个品种之间的相对排名，不是绝对好坏，也不能跨日期直接比较。"),
        ("趋势 / 持仓", "越靠外表示当日相对更强或持仓分位更高。"),
        ("波动 / 尾部风险", "越靠外表示风险相对更高，不应理解成表现更好。"),
        ("流动性冲击 / 拥挤度", "越靠外表示冲击或拥挤风险相对更高；缺数据时不生成分数。"),
    ],
    "数据质量": [
        ("OK", "检查通过，表示该规则未发现问题。"),
        ("WARN", "可以继续查看，但应注意数据滞后、字段缺失或样本不足等限制。"),
        ("ERROR", "关键检查失败，相关研究结论应暂停使用。"),
        ("缺失", "空值表示上游没有可靠数据，不代表真实数值为零。"),
    ],
}


QUADRANT_EXPLANATIONS = {
    "PRICE_UP_OI_UP": "价格上涨、总持仓增加：行情参与度上升，但仅凭总持仓不能确认新增多头还是新增空头。",
    "PRICE_UP_OI_DOWN": "价格上涨、总持仓减少：可能包含空头减仓推动，也可能只是临近换月或整体降仓。",
    "PRICE_DOWN_OI_UP": "价格下跌、总持仓增加：可能有新增空头参与，但仍需席位与期限结构验证。",
    "PRICE_DOWN_OI_DOWN": "价格下跌、总持仓减少：可能包含多头减仓，也可能是整体资金退出。",
}


def _number(value) -> float | None:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value if np.isfinite(value) else None


def _pct(value, digits: int = 1) -> str:
    number = _number(value)
    return "数据缺失" if number is None else f"{number * 100:.{digits}f}%"


def _name(symbol: str, symbol_meta: Mapping[str, Mapping[str, str]]) -> str:
    return f"{symbol_meta.get(symbol, {}).get('name', symbol)}（{symbol}）"


def state_explanation(state: object) -> str:
    key = "DATA_LIMITED" if state is None or pd.isna(state) else str(state)
    return STATE_EXPLANATIONS.get(key, STATE_EXPLANATIONS["TRANSITION"])


def quadrant_explanation(quadrant: object) -> str:
    if quadrant is None or pd.isna(quadrant):
        return "价仓组合数据不足，暂不做解释。"
    return QUADRANT_EXPLANATIONS.get(str(quadrant), "当前价仓组合未进入标准四象限。")


def board_readout(
    latest: pd.DataFrame,
    symbol_meta: Mapping[str, Mapping[str, str]],
    business_lag: int,
    warn_count: int,
) -> dict[str, object]:
    if latest.empty:
        return {
            "headline": "当前没有足够数据生成市场归纳。",
            "facts": [],
            "risk": "等待数据更新后再判断。",
            "changes": "暂无可比较状态。",
        }

    states = latest["market_state"].fillna("DATA_LIMITED") if "market_state" in latest else pd.Series(dtype=str)
    counts = states.value_counts()
    ranked = counts.index.tolist()
    state_words = {
        "HEALTHY_TREND": "趋势较健康",
        "HIGH_FRAGILITY": "高位脆弱",
        "SHORT_SQUEEZE": "空头挤压",
        "LONG_LIQUIDATION": "多头踩踏",
        "NEW_SHORT_TREND": "新空趋势",
        "POTENTIAL_BOTTOM": "潜在筑底",
        "HIGH_NOISE": "高噪声",
        "TRANSITION": "过渡",
        "DATA_LIMITED": "数据受限",
    }
    pieces = [f"{int(counts[state])} 个{state_words.get(state, state)}" for state in ranked[:3]]
    headline = f"当前 {len(latest)} 个品种中，" + "、".join(pieces) + "。"

    facts: list[str] = []
    if "momentum20" in latest and latest["momentum20"].notna().any():
        strongest = latest.loc[latest["momentum20"].idxmax()]
        weakest = latest.loc[latest["momentum20"].idxmin()]
        facts.append(
            f"近 20 日相对最强的是 {_name(str(strongest.symbol), symbol_meta)}（{_pct(strongest.momentum20)}），"
            f"相对最弱的是 {_name(str(weakest.symbol), symbol_meta)}（{_pct(weakest.momentum20)}）。"
        )

    if "cvar95" in latest and latest["cvar95"].notna().any():
        tail = latest.assign(_tail=latest["cvar95"].abs()).nlargest(min(2, len(latest)), "_tail")
        tail_words = [f"{_name(str(row.symbol), symbol_meta)} {_pct(row.cvar95)}" for row in tail.itertuples()]
        facts.append("历史最差 5% 日的平均损失目前较大的是 " + "、".join(tail_words) + "。")

    changed = latest[latest.get("state_change", pd.Series(index=latest.index, dtype=object)).fillna("UNCHANGED") != "UNCHANGED"]
    if changed.empty:
        changes = "与上一交易日相比，8 个品种的状态分类均未变化。"
    else:
        details = [f"{_name(str(row.symbol), symbol_meta)}：{row.state_change}" for row in changed.itertuples()]
        changes = "状态发生变化：" + "；".join(details) + "。"

    if business_lag > 1:
        risk = f"数据已滞后 {business_lag} 个工作日，以下文字只解释最后一个有效交易日，不代表实时市场。"
    elif warn_count:
        risk = f"数据时效正常，但有 {warn_count} 项质量提醒；缺失字段不会被当成 0，也不会生成替代指标。"
    else:
        risk = "数据时效与自动检查均正常；状态仍是研究分类，不是交易指令。"
    return {"headline": headline, "facts": facts, "risk": risk, "changes": changes}


def symbol_plain_readout(row: pd.Series, symbol_name: str) -> str:
    state = row.get("market_state", "DATA_LIMITED")
    momentum = _number(row.get("momentum20"))
    oi = _number(row.get("oi_change_pct"))
    direction = "上涨" if momentum is not None and momentum > 0 else "下跌" if momentum is not None and momentum < 0 else "基本持平"
    oi_word = "增加" if oi is not None and oi > 0 else "减少" if oi is not None and oi < 0 else "变化不明显"
    return (
        f"{symbol_name}近 20 日价格{direction} {_pct(abs(momentum) if momentum is not None else None)}，"
        f"最近一日总持仓{oi_word} {_pct(abs(oi) if oi is not None else None)}。"
        f"当前归为“{state}”：{state_explanation(state)}"
    )


def survival_readout(row: pd.Series, history: pd.DataFrame) -> str:
    rv20 = _number(row.get("rv20"))
    rv60 = _number(row.get("rv60"))
    ratio = rv20 / rv60 if rv20 is not None and rv60 not in (None, 0) else None
    if ratio is None:
        volatility = "波动率数据不足。"
    elif ratio > 1.2:
        volatility = f"近期波动正在升温：20 日波动率为 {_pct(rv20)}，明显高于 60 日水平。"
    elif ratio < 0.8:
        volatility = f"近期波动相对降温：20 日波动率为 {_pct(rv20)}，低于 60 日水平。"
    else:
        volatility = f"近期波动与中期大致接近：20 日波动率为 {_pct(rv20)}。"

    cvar = _number(row.get("cvar95"))
    if cvar is None:
        tail = "CVaR 数据不足，暂不描述尾部损失。"
    else:
        valid = history["cvar95"].dropna().abs() if "cvar95" in history else pd.Series(dtype=float)
        rank = float((valid <= abs(cvar)).mean()) if not valid.empty else np.nan
        rank_text = f"，处于本品种历史约 {rank * 100:.0f}% 分位" if np.isfinite(rank) else ""
        tail = f"进入历史最差 5% 的交易日后，平均单日收益约为 {_pct(cvar)}{rank_text}。"
    return f"{volatility} {tail} 这些指标回答“可能有多颠簸”，不回答“下一步涨还是跌”。"


def positioning_readout(row: pd.Series) -> str:
    quadrant = quadrant_explanation(row.get("price_oi_quadrant"))
    roll = _number(row.get("roll_yield_research"))
    if roll is None:
        structure = "期限结构数据不足。"
    elif roll > 0:
        structure = f"研究口径 Roll Yield 为 {_pct(roll)}，近月价格高于远月。"
    elif roll < 0:
        structure = f"研究口径 Roll Yield 为 {_pct(roll)}，远月价格高于近月。"
    else:
        structure = "近远月价格基本持平。"
    return f"{quadrant} {structure} 期限结构描述供需与持有成本的综合结果，不应单独解释为未来方向。"


def timing_readout(row: pd.Series) -> str:
    momentum = _number(row.get("momentum20"))
    position = _number(row.get("price_pct_120"))
    momentum_text = "20 日动量缺失" if momentum is None else f"近 20 日价格变化 {_pct(momentum)}"
    position_text = "120 日位置缺失" if position is None else f"处于近 120 日约 {position * 100:.0f}% 分位"
    return f"{momentum_text}，{position_text}。{state_explanation(row.get('market_state'))}"


def analog_readout(analogs: pd.DataFrame) -> str:
    if analogs.empty:
        return "没有足够的历史相似样本，暂不做情景归纳。"
    future = analogs["future_return_20d"].dropna()
    drawdown = analogs["future_max_drawdown"].dropna()
    if future.empty:
        return "找到相似日期，但其后 20 日结果不足，不能形成统计归纳。"
    positive = float((future > 0).mean())
    median = float(future.median())
    worst = float(drawdown.min()) if not drawdown.empty else np.nan
    worst_text = "数据不足" if not np.isfinite(worst) else _pct(worst)
    return (
        f"在这 {len(analogs)} 个相似历史样本中，{positive * 100:.0f}% 的样本随后 20 日上涨，"
        f"20 日收益中位数为 {_pct(median)}，窗口内最差回撤为 {worst_text}。"
        "这是一组历史情景分布，不是当前行情的概率预测。"
    )

