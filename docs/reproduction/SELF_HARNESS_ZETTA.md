# Self-Harness / Zetta

- **状态：L1 源码与协议核验。**
- Zetta 上游提交：`74527e7`（审计副本）。
- Self-Harness 用于定义失败挖掘、critic 更新、恢复技能更新和验证门控的闭环；当前没有可直接套用到本项目的统一固定数值入口。

## 可借鉴内容

主系统冻结后才开启 harness 更新。每轮更新必须通过跨分布回归测试；若 ID 提升但 OOD 风险、误报率或查询成本退化，则拒绝更新。这样避免自进化把验证器过拟合到新近失败。

## 未达到指标复现的原因

Zetta 的完整协议依赖 LIBERO-Pro/Pi0.5、RoboCasa/GR00T 或 RoboTwin 等策略与环境组合。仅运行仓库单元测试不等于复现完整自进化增益。Self-Harness 本身更接近通用方法框架，不提供与本任务一一对应的冻结基线。

结论：二者用于后期闭环设计和回归门控，不进入第一阶段主结果表。

来源：https://github.com/air-embodied-brain/Zetta-Embodiment
