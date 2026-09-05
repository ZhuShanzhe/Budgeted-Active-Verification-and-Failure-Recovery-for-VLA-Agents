# 数据准备与基线实验记录

本轮实验围绕“预算约束的主动多模态证据获取、验证与失败恢复”准备可运行对照。策略、critic、世界模型和数据生成器分别记录，不把不同问题的分数混为一张排名表。

本页保留首轮实验范围；同日后续已补齐 [SAFE DROID](SAFE_DROID_20260905.md) 和 [距离型检测器](EXTENDED_BASELINES_20260905.md)。最新状态以 [复现总表](README.md) 为准，下文早期资源缺失描述不代表当前仍然缺失。

## 已完成的定量结果

| 角色 | 实现与数据 | 本轮实测 | 范围 |
|---|---|---|---|
| 固定执行策略 | OpenVLA-OFT / 原版 LIBERO Spatial | 50/50 成功，100% | 10 任务 × 5 初始状态，seed 7 |
| 视觉策略参考 | AVA-VLA / 同一组 Spatial 状态 | 48/50 成功，96% | 与 OFT 配对；不是 ActiveVLA |
| 内部特征 critic | SAFE-MLP / WidowX | 未见任务报警 AUROC 0.8185 ± 0.0367 | 3 个任务划分/训练种子，固定配置 |
| 时序 critic | SAFE-LSTM / WidowX | 同口径 AUROC 0.6278 ± 0.0099 | 同上 |
| 世界模型/value 基线 | WCM / 官方 pick-place 验证集 | value RMSE 0.380342；Pearson 0.720664 | 前一轮已完成；18 episode、1,617 窗口，本轮未重复跑 |

OFT/AVA 使用公开权重；SAFE 是本轮实际训练的模型。Spatial 仅为有限样本评测；SAFE 没有完整超参数网格搜索；WCM 仅覆盖公开 quick benchmark。以上均不表述为整篇论文全任务结果复现。

七维 LIBERO-Plus 的固定 70 任务子集已完成：OFT 58/70（82.86%），AVA 55/70（78.57%）。协议预先按七类扰动各抽 10 个任务，抽样种子 20260905、每任务 1 次，同一名单用于两个策略；不根据模型成绩选择任务。配对审计确认两种策略的任务、提示词及初始状态索引完全一致，全部 240 次标准/扰动策略执行均无基础设施错误。

协议审计发现：当前 Plus 上游会把部分非语言扰动的 `view`、`initstate`、`table` 等后缀写入策略提示词。原样运行可复核发布实现，但不是严格的单一视觉因素控制实验。本批 Plus 结果归为实现诊断；在冻结论文用单因素协议前，不能把下降全部归因于视觉扰动，也不能直接作为本方法论文主 OOD 表。

## 数据与环境验证

- 原版 LIBERO 四套件全部下载并通过官方 SHA-256 及结构检查：40 文件、2,000 条演示、338,575 个动作步、33.78 GB。清单与路径见 [数据记录](DATASETS_20260905.md)。
- ManiSkill3 抓取、堆叠、侧向插入演示：39 文件、255.55 MB，完整落盘并建立哈希清单。
- 三类任务均通过 RGB-D、状态与环境结果字段检查；每类重放 3 条官方动作演示，9/9 成功。不是学习模型性能。
- FailGen 完成 8 次程序化扰动执行，实际成功 4 条、失败 4 条。只验证生成链路，不构成已训练 AHA 模型。
- WidowX 532 条真实轨迹已校验、解压并用于 SAFE；DROID 缺失不阻塞本轮实验。

## 本轮直接结论

1. 标准 Spatial 上两个公开策略已经能够闭环执行。当前小样本成绩接近饱和，不能只依赖标准环境成功率评价验证方法。
2. SAFE 的完整评测窗口报警排序与较早时刻的失败检出能力不同；已分别保存时刻指标、最大报警指标及检测时间曲线。窗口按官方任务最短轨迹长度定义，不等于每条轨迹自己的完整长度。
3. 校准水平不等于跨任务误报率保证。alpha=0.10 时，MLP 三个未见任务划分的实测误报率为 53.23%、1.64%、14.52%。这属于当前基线现象，不是本项目已解决的新贡献。
4. 外部演示可用于环境与表征准备，但不能代替同一状态下多种观察、真实查询成本、失败时刻和恢复结果的配对数据。FailGen 当前图像输出仍需扩充统一时序字段。

## 复现证据与运行入口

- [SAFE 完整记录](SAFE_20260905.md)：固定配置、划分、AUROC/AUPRC、校准与输入权限。
- [策略记录](OPENVLA_AVA_VLA.md)：原版环境隔离、权重范围、初始状态、成功率与计时边界。
- [AHA/FailGen](AHA_FAILGEN.md)：实际运行范围与依赖修正。
- [WCM](WCM.md)：已有验证结果与适用范围。
- `docs/reproduction/results/20260905/`：配置、逐轨迹结果、划分、校准表、源码提交、依赖版本。
- `results/20260905/artifact_audit.json`：44 个权重/配置文件指纹；18 份 SAFE 预测数组的有效值与标签检查通过，同种子的 MLP/LSTM 使用完全相同划分。
- `results/20260905/paired_policy_audit.json`：标准及扰动测试的逐例配对、各类成功数与配对一致性检查。
- `manifests/`：数据文件、字节数、revision 与 SHA-256。
- 服务器完整实验目录：`/root/autodl-tmp/experiments/baselines-20260905/`，保存模型权重、分数数组和视频。

```bash
bash scripts/run_safe_baseline_matrix.sh
/root/autodl-tmp/conda-envs/vla-safe/bin/python scripts/eval_saved_safe.py
bash scripts/run_policy_matrix.sh
bash scripts/replay_maniskill_demos.sh
/root/autodl-tmp/conda-envs/vla-safe/bin/python scripts/collect_baseline_audit.py
python scripts/audit_policy_results.py
```

策略评测脚本拒绝覆盖已有逐轨迹结果；重复实验时必须使用新的 `--output` 目录，不能直接混写本批路径。

所有正式结果与早期失败尝试分目录保存。未公开可执行模型或缺少依赖条件的工作继续保留为相关工作/工程参考，不虚构指标；状态总表见 [README](README.md)。大型数据、权重和视频没有提交到 Git 仓库。
