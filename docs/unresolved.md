# 当前未解决事项

## 真正依赖外部权限

- CTP：Broker ID、User ID、密码、行情前置地址；部分柜台还需 Auth Code 与 App ID。
- 或稳定实时 API/WebSocket：URL 与 Token。

## 不依赖权限但受上游数据可得性限制

- JM/J/RB/HC/LC/SI/PS 的公开连续源不提供历史主力合约代码，因此当前只展示真实价格事实，不进入风险、状态和相似度研究。
- 当前公开源无成交额，Amihud 为 NULL；不能用成交量伪代。
- Top20、可靠现货基差和明确商品 benchmark 尚未接入，对应拥挤度、Basis Momentum、Co-moments 保持缺失。
- 无真实分钟/Tick，OFI、POC、盘口不平衡和价格冲击保持禁用。
- 多晶硅上市时间短，长期窗口和 walk-forward 必须按实际样本标记不足。
- DCE 官方日终接口在 2026-09-06 实测返回非 JSON；公开 API 作为有记录的 Tier-4 降级源。

## 回测限制

- 当前可审计本地证据仅覆盖铁矿石 2020-01-02 至 2026-09-04。
- 2023 年后 10%/20 日的高位顶部正样本缺失，walk-forward 的测试窗 AUC 多数不可识别；Brier/Log Loss 仍输出，AUC 明确标 `insufficient_test_classes`。
