# SAFE

- **状态：L1 工程核验。**
- `third_party/SAFE` 与 `third_party/SAFE-openvla` 已安装。
- Hydra 配置、包导入和训练/评测入口可启动。
- 尚未用冻结 rollout 训练 detector，也未得到 AUROC、AUPRC、FPR 或 conformal coverage。

## 可借鉴内容

SAFE 的 VLA 内部特征、跨任务失败检测和 conformal prediction 构成本项目轻量 critic 与校准报警基线。主实验将额外报告风险覆盖曲线、误报成本和预算耗尽时的选择性风险。

## 未达到指标复现的原因

论文级结果需要与指定策略严格对齐的成功/失败 rollout、内部特征抽取和 detector 训练。仅启动入口不构成 SAFE 指标复现。

## 数据

上游提供两组 Google Drive rollout：Pi0-FAST 与 OpenVLA/WidowX。下载状态与人工处理要求见 [DATASETS.md](DATASETS.md)。
