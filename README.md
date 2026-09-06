# Commodity Quant Agent

面向黑色与新能源期货的可审计量价研究系统。当前实现已经覆盖真实公开日线采集、单合约主力治理、DuckDB、指标、事件研究、单因子分组、walk-forward、状态识别、相似状态、Streamlit 看板和日报输出。

## 快速开始

```powershell
$py = 'C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
cd commodity_quant_agent
& $py -m scheduler.bootstrap --start 20200101
& $py -m scheduler.daily_report
& $py -m streamlit run dashboard/app.py
```

跨电脑临时访问和长期部署见 `docs/deployment.md`；公网模式支持通过 `DASHBOARD_PASSWORD` 启用登录保护。

首次运行会从公开 API 下载 8 个品种的真实单合约日线。系统按成交量优先、持仓量辅助、20% 挑战阈值和 2 日确认生成主力序列；换月日收益使用新主力自身昨收，研究价格采用向前加差复权，杜绝把合约跳空计入波动率和尾部风险。

如果公开网络不可用，可先运行 `python -m scheduler.bootstrap --offline`，它只读取已经缓存的数据。任何模拟流都带 `source=SIMULATED_REALTIME`，不能写入真实行情表。

## 数据源与边界

优先级固化为 CTP > 实时 API/WebSocket > 交易所日终 > 公开 API > 网页兜底。当前无 CTP/API 凭证，因此：

- `I/JM/J/RB/HC/LC/SI/PS`：全部使用真实单合约公开日线，保留原始合约、主力合约、前后合约、roll flag 和复权方法；
- 当前特征库共 10,163 个主力交易日、145 次受治理换月；新能源品种按实际上市时间起算，不伪造上市前样本；
- 成交额、Top20、基差、分钟/Tick 当前缺失，相关指标为 NULL 并记录原因；
- OFI/POC 等微观结构指标严格只接受真实分钟/Tick 数据。

密钥只从环境变量读取，见 `.env.example`。

## 主要命令

```powershell
python -m scheduler.update_daily
python -m scheduler.update_intraday --simulate --ticks 60
python -m backtest.report
python -m scheduler.daily_report
python -m pytest -q
```

浏览器视觉检查（需本机已有 Playwright 与 Edge）：

```powershell
$env:DASHBOARD_PASSWORD='你的看板密码'
node scripts/dashboard_visual_check.cjs
```

输出位置：

- DuckDB：`data/commodity_quant.duckdb`
- 特征：`data/feature_store/*.parquet`
- 回测：`reports/backtest/`
- 日报：`reports/daily/YYYY-MM-DD.json|md`
- 数据质量：`reports/data_quality/`

## 结果治理

所有结构化输出区分 `data_facts`、`calculation_results`、`research_interpretation`、`hypotheses_to_validate`。数值只来自计算引擎；解释层不估算统计数值。证据字段区分 `local_evidence` 与 `external_evidence`。

## 当前仍需用户提供

只有接入实时生产链路才需要：CTP Broker ID、User ID、行情前置地址及相应认证信息，或稳定实时 API/WebSocket Token。Tushare Token 是可选项，并非当前历史回测的阻塞项。
