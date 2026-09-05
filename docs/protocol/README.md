# 程序化主动验证：协议与采集入口

本模块服务于“预算约束的主动多模态证据获取、VLA 验证与失败恢复、跨分布泛化”。决策的表达形式改为可解释、可检查的程序；研究对象没有转为通用代码生成。

主策略保持冻结。新增模块负责获取证据、估计风险、决定继续或恢复。离线 coding agent 利用开发集案例改写决策程序；固定执行器负责工具权限与预算，独立评测负责验收。生成程序无权修改标签、数据划分、critic 或评测器。

## 文件导航

| 文件 | 内容 |
|---|---|
| [PROTOCOL_V1.md](PROTOCOL_V1.md) | 比较规则、分布划分、成本口径、结论边界 |
| [TRACE_SCHEMA.md](TRACE_SCHEMA.md) | 轨迹格式、监督标签、恢复分支与训练读取 |
| [CODING_HARNESS.md](CODING_HARNESS.md) | 决策程序接口、失败反馈、代码变更验收 |
| [REPORT_REQUIREMENTS_COVERAGE.md](REPORT_REQUIREMENTS_COVERAGE.md) | 研究报告要求与当前实现逐项核对 |
| [RUNBOOK.md](RUNBOOK.md) | 服务器上的执行入口和数据位置 |
| [PIPELINE_ACCEPTANCE_20260905.md](PIPELINE_ACCEPTANCE_20260905.md) | 本次真实测试结果与限制 |
| [DATA_PREPARATION_CONTINUATION.md](DATA_PREPARATION_CONTINUATION.md) | DROID 接入、监督有效掩码、多任务可续跑采集 |

实现位于仓库 `bav/`，机器可读协议位于 `configs/protocol_v1.json`，参考决策程序位于 `programs/`，自动测试位于 `tests/`。

本轮交付是可运行的采集与验证基础设施和小规模验收数据，不是新的模型论文结果，也不是已经完成全部训练数据或自动自进化系统。未训练的 critic、不存在的语义失败标签、未配置的外部模型均显式留空，不生成替代分数。
