# SAFE：Pi0-FAST / DROID 补充复现

## 数据来源与边界

本次使用用户已下载的 `pi0fast_droid_0510_all.zip`，不是整个原始 DROID 通用数据集，也不是 Pi0-FAST 模型权重。该包是 SAFE 作者发布的真实机器人 rollout、内部特征和视频记录。

文件大小 27,370,430,312 字节，约 25.49 GiB；本地与服务器 SHA-256 一致，均为 `5dbf96099a2bc5d4bb23c6a58e028822c62288d4691e2f8ab1dcd7ed223f51d1`。74,337 个 ZIP 条目已完成解压和 CRC 检查，解压字节数 49,228,250,264，顶层目录为 rollouts_all。

目标原包：`/root/autodl-tmp/datasets/safe-rollouts/pi0fast_droid_0510_all.zip`。

目标解压目录：`/root/autodl-tmp/datasets/safe-rollouts/droid-extracted-v1/`。

既有 `.zip.part` 不计作完整数据，不覆盖也不删除。

## 冻结配置

实验沿用官方 `pizero_fast_droid_0510` 配置和官方 LSTM、MLP（indep）实现。输入是 `pre_logits` 的 token 均值，不是只看 RGB 的黑盒失败检测。固定 batch 64、学习率 1e-4、1,000 epoch；LSTM 正则 0.001，MLP 正则 0.01；随机种子 0、1、2。关闭全数据特征标准化与 W&B 上传。

配置在读取新测试成绩前确定，使用最终 epoch 权重，不按未见任务分数挑选 checkpoint；不是作者全部网格的穷举或最佳论文数值保证。

作者配置采用 full_length_only、每任务成败平衡到约 50%、最多 60 条、未见任务比例 0.25、已见任务训练比例 0.75。实际保留数量在载入后记录。它不是原始自然成功率或全包全部轨迹；筛选前后的数量与类比例分开报告。三种种子同时影响划分和训练，标准差不是纯训练随机性。

## 验收口径

每组训练保存配置、精确划分名单、日志和最终权重。随后重新加载权重，核对划分一致性，导出逐轨迹分数、AUROC/AUPRC、校准表及 alpha=0.10 的实测 FPR/TPR。训练路径与测试路径不得重叠，训练任务与未见任务不得重叠。

SAFE 的 early-stop 指标为任务统一窗口内的最大报警分数；时刻指标与它分开。AUPRC 使用作者实现的曲线积分口径，不替换为 average precision。校准阈值跨任务的表现是实测结果，不能宣称任意 OOD 下自动满足 nominal alpha。

## 当前状态

全包已上传，两端 SHA-256 一致，74,337 个条目已完成解压与逐文件 CRC 检查。原始元数据审计发现 15 条标签异常，包括 5 条介于 0 与 1 之间的值、10 条二元元数据与文件名不同的记录。作者读取器使用 `int(env_record["episode_success"])`，不以文件名为标签；本次官方复现沿用此规则，原文件不改。异常表随数据审计保存，后续新模型可靠监督须排除或经独立审核，不宣称这 15 条的真实成败已被修正。

六组 1,000 epoch 训练、最终权重重新加载测试、逐轨迹分数导出、校准评测和标签异常敏感性测试均已完成。独立测试与训练结束保存的对应 AUROC/AUPRC 数值逐组一致（最大绝对差 0）。不是只完成训练入口或单次前向。

原始 1,464 条轨迹，13 个任务描述，按作者标签读取规则为 558 成功、906 失败。官方筛选后固定为 780 条、390 成功与 390 失败；每种子 train 450、val_seen 150、val_unseen 180，未见任务 3 个，训练任务 10 个。路径和任务隔离检查通过。

## 未见任务结果

下表为三种子的均值 ± 样本标准差，失败为正类。种子同时改变训练及任务划分。

| 检测器 | early-stop AUROC | early-stop AUPRC | 统一窗口末端 AUROC |
|---|---:|---:|---:|
| SAFE LSTM | 0.5358 ± 0.0208 | 0.5393 ± 0.0475 | 0.5768 ± 0.0471 |
| SAFE MLP | 0.5353 ± 0.0445 | 0.6134 ± 0.0300 | 0.5353 ± 0.0445 |

校准使用已见任务成功轨迹，nominal alpha=0.10；以下是未见任务统一窗口末端（`at earliest stop`）实测值，不是校准承诺，也不是“窗口内曾经报警”的累计误报率。上表 early-stop AUROC/AUPRC 则取该窗口内最大分数（`by earliest stop`），两种口径分开报告。

| 检测器 / 种子 | FPR | TPR |
|---|---:|---:|
| LSTM / 0 | 0.2222 | 0.2889 |
| LSTM / 1 | 0.0889 | 0.2222 |
| LSTM / 2 | 0.3444 | 0.3667 |
| MLP / 0 | 0.2889 | 0.3222 |
| MLP / 1 | 0.1556 | 0.2667 |
| MLP / 2 | 0.2667 | 0.3444 |

该固定配置下跨任务排序接近随机，已见任务 early-stop AUROC 为 0.6275–0.7452，存在明显泛化下降。它不代表 SAFE 全部配置的最佳能力，也不构成新方法有效的证据。未利用这批测试分数回调参数。

15 条原始标签异常中，8 条进入官方 780 条集合。敏感性测试固定原训练权重，仅从评测和校准子集排除异常：种子 0 的未见测试不移除，种子 1、2 各移除 1 条；各校准集移除 2 条。排除后的 early-stop AUROC 为 LSTM 0.5387 ± 0.0205、MLP 0.5361 ± 0.0455，未改变本配置下泛化较弱的结论。敏感性结果另存 `sensitivity_excluding_label_issues.json` 和 `sensitivity__*.json`，不覆盖官方主结果。这不是清洗后重训，不能用来排除异常训练标签的影响。

一条腕部视频的标准文件名链接缺失，压缩包内另有非标准命名记录。未擅自改名，外部视觉接口在视频对齐审核前不生成时间步监督。

完整小型结果与溯源见 [结果汇总](results/20260905/safe-droid-v1/summary.json) 和 [校准表](results/20260905/safe-droid-v1/conformal_alpha01.json)。逐轨迹分数 NPZ、最终权重保留在服务器各实验目录，原始数据不进入 Git。

状态文件：`/root/autodl-tmp/datasets/safe-rollouts/droid-completion-status.json`。

完成日志：`/root/autodl-tmp/logs/droid_completion_v2.log`；补充测试日志：`/root/autodl-tmp/logs/droid_sensitivity_v1.log`。首次严格审计停止的日志保留，未伪装为成功运行。

入口：`scripts/complete_droid_upload.py`、`scripts/run_safe_droid_matrix.sh`、`scripts/eval_saved_safe.py`、`scripts/export_safe_droid.py`。

## 与主研究的关系

本批补齐另一策略和真实机器人域上的失败检测对照。它不意味着将 WidowX 训练的模型零样本迁移到 DROID；本批各域独立训练，也不把 DROID 白盒特征分数直接当作 LIBERO critic。视频可供后续外部视觉验证使用，但没有可重置物理状态，不能用离线视频伪造主动换视角或恢复的反事实结果。

来源：仓库已固定的 [SAFE 官方实现](https://github.com/vla-safe/SAFE)，其中 `failure_prob/conf/dataset/pizero_fast_droid_0510.yaml` 与 `scripts/batch_training/submit_pi0fast_droid.bash` 定义本次数据与对照来源。
