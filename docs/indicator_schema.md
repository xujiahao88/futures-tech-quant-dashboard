# 指标 Schema

## Survival Layer

`return, atr14, rv5/10/20/60, skew20/60/120/250, kurtosis20/60/120/250, var95/99, cvar95/99, max_drawdown_250, drawdown_duration, amihud, vol_cone_p10/p50/p90_*`。

VaR/CVaR 为历史模拟左尾收益；95% 至少 100 个样本，99% 至少 500 个样本。否则数值为 NULL、`var99_sample_status=insufficient_sample`。

## Positioning Layer

`oi_level, oi_change, oi_change_pct, oi_percentile_250, price_oi_quadrant, volume_oi, spread, roll_yield_user, roll_yield_research, basis_momentum_20, top20_long/short/net/net_ratio, crowding_percentile`。

用户口径 `(far-near)/near`；研究方向口径 `(near-far)/near`。

## Timing Layer

`ma5/10/20/60, ma_slope_*, momentum5/10/20/60, momentum_acceleration, price_pct_20/60/120/250, hurst_rs_120, fractal_katz_120, rv_term_structure, relative_strength, breadth, black_breadth, new_energy_breadth`。

Hurst 算法字段固定 `R/S`；Fractal 算法字段固定 `Katz`，不与其他算法序列拼接。

## Higher Moments

`co_skewness, co_kurtosis, benchmark_name` 仅在明确 benchmark 且数据可用时生成。当前不静默替换文华商品指数，因此未生成。

## Microstructure

`ofi, bid_ask_imbalance, price_impact, volume_profile, poc` 只接收 `is_simulated=false` 的真实分钟/Tick。日线和模拟流会触发硬错误。
