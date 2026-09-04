# Baseline 复现总表

本目录按“可写入论文的证据强度”记录基线状态。仓库存在、依赖安装成功或单次前向通过，均不等同于论文结果复现。

审计日期：2026-09-04。上游仓库后续更新时重新核验。

## 判定标准

- **L3 指标复现**：使用公开权重、规定数据与官方协议，得到可对照的定量指标。
- **L2 链路复现**：真实模型、真实环境或真实数据完成端到端执行，但尚未跑完整评测。
- **L1 工程核验**：代码、配置、数据格式或入口通过；不能作为论文数值基线。
- **L0 未复现**：关键代码、权重、数据、硬件或协议缺失。

## 当前状态

| 工作 | 状态 | 已取得的证据 | 能否作为论文数值基线 |
|---|---:|---|---:|
| OpenVLA-OFT | L2 | 官方 7.54B LIBERO-Spatial 权重完成真实单步前向，输出 `(8, 7)` 且有限 | 否，需完整 rollout |
| AVA-VLA | L2 | 官方 7.54B 4-in-1 权重完成真实单步前向，输出 `(8, 7)` 且有限 | 否，需完整 rollout |
| ActiveVLA | L0 | 上游仓库仅有说明和素材，代码、权重、评测仍标为待发布 | 否 |
| AHA / FailGen | L1 | AHA 仓库与 57 条 REFLECT 子集可读取；未获得最终 AHA 权重 | 否 |
| SAFE | L1 | 环境、包和 Hydra 入口通过；未训练/评测 detector | 否 |
| ADV / VeGAS | L0 | 论文可读，未找到作者发布的可执行官方实现 | 否 |
| WCM | L3（公开 quick benchmark） | 官方数据、episode split 与权重完成 1,617 个窗口/18 个 episode 的完整验证 | 是，仅限公开 pick-place 协议 |
| VAP-TAMP | L1 | 源码可审计；完整系统依赖 ROS2、OmniGibson、API 与实体平台 | 否 |
| Thea | L1 | 公开预览代码可审计；论文级仿真结果依赖用户提供策略与评测器 | 否 |
| Self-Harness / Zetta | L1 | Zetta 代码可审计；Self-Harness 是方法框架，缺少统一可复现数值入口 | 否 |
| LIBERO-Plus | L2 | 官方约 16 GB 资产安装，EGL 环境与双相机渲染通过 | 否，需七维完整协议 |

## 论文使用规则

只有 L3 结果进入主结果表。L2 可写入“系统实现与可运行性”，L1 仅用于工程设计依据或消融入口，L0 只能作为相关工作。任何后续升级都必须在对应文档中补充：代码提交、环境、数据修订版、命令、日志、随机种子和指标。

## 文件索引

- [OpenVLA-OFT 与 AVA-VLA](OPENVLA_AVA_VLA.md)
- [ActiveVLA](ACTIVEVLA.md)
- [AHA / FailGen](AHA_FAILGEN.md)
- [SAFE](SAFE.md)
- [ADV / VeGAS](ADV_VEGAS.md)
- [WCM](WCM.md)
- [VAP-TAMP](VAP_TAMP.md)
- [Thea](THEA.md)
- [Self-Harness / Zetta](SELF_HARNESS_ZETTA.md)
- [LIBERO-Plus](LIBERO_PLUS.md)
- [数据集清单](DATASETS.md)
