# AHA / FailGen

- **状态：AHA 模型 L1；ManiSkill-FailGen 数据生成 L2（2026-09-05）。**
- AHA 源码已纳入 `third_party/AHA`。
- 仓库内 57 条 REFLECT 子集可正确读取，可用于失败文本结构和标签设计检查。
- 尚未获得可直接评测的最终 AHA detector/critic 权重。

## 本次实际运行

`third_party/maniskill-failgen` 已固定为 Git 子模块。在 PickCube、StackCube 两类任务上完成 8 次有限次数的失败注入：grasp、trans_x 两类扰动，种子 7、8，各任务各扰动执行 2 次。8 次执行函数均正常返回，读取环境终局结果得到成功 4 条、失败 4 条。这是数据生成链路检查，不是 AHA critic 准确率，也不是完整 FailGen 数据集。

记录位于服务器 `/root/autodl-tmp/experiments/baselines-20260905/failgen-smoke/summary.json`，图像位于同目录 `generated/`。上游保存入口主要输出多视角拼接帧；其 HDF5 轨迹保存被上游关闭，不能把当前小型样本描述为包含完整动作、状态、成本字段的正式训练集。没有把“注入扰动”直接作为失败标签。

兼容配置：ManiSkill 3.0.1、SAPIEN 3.0.3、Gymnasium 0.29.1、NumPy 1.26.4、SciPy 1.14.1、OpenCV 4.11.0.86、MPlib 0.1.1。适配了 ManiSkill 移动后的 motionplanning 工具模块路径。原 NumPy 2.3.2 组合在 MPlib 构造时发生原生崩溃；切换上述兼容组合后完成 8 次运行。固定为 CPU 物理仿真与 GPU 渲染。

复现入口：`scripts/smoke_failgen.py`。失败排障日志保留在 `/root/autodl-tmp/logs/failgen_*`，成功日志为 `failgen_smoke_v4.log`。

## 可借鉴内容

FailGen 的程序化失败注入和自然语言失败原因用于构建跨扰动失败轨迹；标签分为失效时刻、失效类型、可见证据和恢复动作，避免只保留二元成功/失败标签。

## 未达到指标复现的原因

FailGen 数据主要通过 CoppeliaSim 4.1、RLBench 或 ManiSkill 流水线生成，不是一个可直接下载后即评测的固定全集。AHA 最终权重与完整论文评测入口未随仓库公开。约 291 GB 的 RoboPoint 联合训练数据与本项目主验证任务不成比例，未下载。

结论：AHA 目前不是数值 critic 基线；FailGen 的小型失败生成链路已经打通，但仍需补齐统一的时序、证据成本、动作与恢复结果字段后才能进入本项目正式训练数据。
