# SAFE

## 当前结果（2026-09-05）

已完成 OpenVLA/WidowX 上 LSTM、MLP 各 3 个种子的 1,000 epoch 训练、独立测试和校准表导出。详见 [定量实验记录](SAFE_20260905.md)。固定配置下未见任务最大报警分数 AUROC 分别为 0.6278 ± 0.0099、0.8185 ± 0.0367。不是论文全量超参数搜索结果。

Pi0-FAST/DROID 也已完整上传、双端哈希与 CRC 校验，完成 LSTM、MLP 各 3 种子训练、独立测试与标签异常敏感性评测。未见任务 early-stop AUROC 分别为 0.5358 ± 0.0208、0.5353 ± 0.0445；详见 [DROID 补充复现](SAFE_DROID_20260905.md)。下面的环境与下载排障记录仅为历史背景，不代表仍需下载。

## 历史工程核验记录

- **2026-09-04 状态：L1 工程核验。**
- `third_party/SAFE` 与 `third_party/SAFE-openvla` 已安装。
- Hydra 配置、包导入和训练/评测入口可启动。
- 尚未用冻结 rollout 训练 detector，也未得到 AUROC、AUPRC、FPR 或 conformal coverage。

## 可借鉴内容

SAFE 的 VLA 内部特征、跨任务失败检测和 conformal prediction 构成本项目轻量 critic 与校准报警基线。主实验将额外报告风险覆盖曲线、误报成本和预算耗尽时的选择性风险。

## 未达到指标复现的原因

论文级结果需要与指定策略严格对齐的成功/失败 rollout、内部特征抽取和 detector 训练。仅启动入口不构成 SAFE 指标复现。

## 数据

上游提供两组 Google Drive rollout：Pi0-FAST 与 OpenVLA/WidowX。下载状态与人工处理要求见 [DATASETS.md](DATASETS.md)。

服务器直连 Google Drive 会超时，`/etc/network_turbo` 代理访问 Google 下载域名会返回 503。仓库提供 `notebooks/colab_fast_safe_rollouts_v2.ipynb`：在 Google Colab 中运行后，数据先进入 Colab 临时磁盘，再通过原生 `rsync` 断点续传至服务器；每完成一个文件立即删除 Colab 副本。文件不经过用户电脑，也不占用本地下载流量。Notebook 固定校验服务器 ED25519 指纹，密码使用隐藏输入且不写入文件。旧版 SFTP 会话必须先终止，避免 Colab 持续恢复旧执行状态。

当公共文件触发 Google Drive 的热门文件下载配额时，改用 `notebooks/colab_drive_copy_safe_rollouts_v3.ipynb`。先在 `drive.google.com` 将一份 ZIP 制作成个人副本并放入 `我的云端硬盘/SAFE-rollouts`，V3 挂载个人 Drive 后直接通过 `rsync` 续传到服务器。可逐个文件处理，以减少个人 Drive 空间需求。

如果网页只允许“添加快捷方式”，使用 `notebooks/colab_create_safe_drive_copy_v4.ipynb` 调用 Google Drive API 的 `files.copy`，直接尝试按原始文件 ID 创建个人副本。快捷方式菜单中的“复制”只会复制快捷方式，不会产生新的数据文件或下载配额。
