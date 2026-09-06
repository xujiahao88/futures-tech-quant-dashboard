SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS daily_bars (
    trade_date DATE, symbol VARCHAR, contract VARCHAR,
    open DOUBLE, high DOUBLE, low DOUBLE, close DOUBLE, adjusted_close DOUBLE,
    settlement DOUBLE, volume DOUBLE, turnover DOUBLE, open_interest DOUBLE,
    open_interest_change DOUBLE, main_contract VARCHAR, roll_flag BOOLEAN,
    previous_contract VARCHAR, next_contract VARCHAR, adjustment_method VARCHAR,
    adjustment_value DOUBLE, true_contract_return DOUBLE, analysis_return DOUBLE,
    source VARCHAR, source_tier INTEGER, is_simulated BOOLEAN, lineage_status VARCHAR,
    PRIMARY KEY (trade_date, symbol)
);
CREATE TABLE IF NOT EXISTS features_daily AS SELECT * FROM daily_bars WHERE 1=0;
CREATE TABLE IF NOT EXISTS data_quality (
    checked_at TIMESTAMP, symbol VARCHAR, dataset VARCHAR, severity VARCHAR,
    check_name VARCHAR, details VARCHAR
);
CREATE TABLE IF NOT EXISTS pipeline_runs (
    run_id VARCHAR, started_at TIMESTAMP, finished_at TIMESTAMP,
    status VARCHAR, data_cutoff DATE, details VARCHAR
);
CREATE TABLE IF NOT EXISTS realtime_ticks (
    event_time TIMESTAMP, symbol VARCHAR, contract VARCHAR, bid DOUBLE, ask DOUBLE,
    bid_size DOUBLE, ask_size DOUBLE, last_price DOUBLE, turnover DOUBLE,
    volume DOUBLE, open_interest DOUBLE, source VARCHAR, is_simulated BOOLEAN
);
"""
