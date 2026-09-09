# 数据 Schema

## daily_bars

主键 `trade_date, symbol`。字段包括 OHLC、`settlement`、`volume`、`turnover`、`open_interest`、`open_interest_change`；治理字段包括 `contract`、`main_contract`、`roll_flag`、`previous_contract`、`next_contract`、`adjustment_method`、`adjustment_value`、`true_contract_return`、`analysis_return`、`lineage_status`；来源字段包括 `source`、`source_tier`、`is_simulated`。

`true_contract_return` 始终按当日主力合约相对该合约上一交易日收盘计算。`analysis_return` 来自向前加差连续价格。供应商黑盒连续序列的两个收益字段均为 NULL，`research_eligible=false`。机械清洗写入 `cleaning_flags`；原始值仍保留在 `data/raw`。

## term_structure

`trade_date, symbol, near_contract, near_price, far_contract, far_price, spread, roll_yield_user, roll_yield_research`。两种收益率口径不得合并。

## realtime_ticks

`event_time, symbol, contract, bid, ask, bid_size, ask_size, last_price, turnover, volume, open_interest, source, is_simulated`。模拟流只能进入隔离表 `simulated_realtime_ticks`。

## holdings

预留：`trade_date, symbol, contract, top20_long, top20_short, top20_net, top20_net_ratio, source`。

## data_quality

`checked_at, symbol, dataset, severity, check_name, details`。
