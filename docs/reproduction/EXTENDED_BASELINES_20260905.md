# SAFE 补充对照：距离型失败检测

## 完成范围

已完成官方 SAFE EmbedModel 的 cosine、Euclidean 两种距离，在 WidowX、DROID 各 3 个既定种子上的 12 组实验。没有替换成自写分类器，未使用测试集选择超参数。

训练数据、轨迹筛选、split seed 0/1/2 与前述 LSTM、MLP 完全一致，并逐路径核验。失败为正类，WidowX 输入 4096 维、DROID 输入 2048 维策略白盒特征；两域独立建立特征库，不是跨策略零样本迁移。

## 固定配置

- 官方实现：`failure_prob.model.embed.EmbedModel`；SAFE 提交 `b6036abe07b2b2bb9996afb2c07f13d6a9f507c0`。
- `topk=5`，`use_success_only=False`，`cumsum=False`；不进行全数据标准化。
- 仅使用训练轨迹的有效时间步建立成功/失败特征库；风险为到成功库的距离减去到失败库的距离。
- 官方 `train_epoch` 建立特征库，不进行梯度优化，因此不填写虚构训练 epoch。
- 特征库是普通 tensor 属性，不在上游 state_dict 中自动持久化；本次显式保存库并记录 SHA-256。
- 保存后重新加载，完整重算 val_seen 和 val_unseen 分数；12 组最大绝对差均为 0。
- 不从训练分数推断泛化，因为训练查询可能命中特征库中的自身。

## 实测结果

以下为未见任务结果，三种子均值 ± 样本标准差。early AUROC/AUPRC 取任务最短轨迹长度定义的统一窗口内最大风险分数；AUPRC 是曲线积分而非 average precision。

| 域 | 距离 | early AUROC | early AUPRC | 窗口 50% 时刻 AUROC |
|---|---|---:|---:|---:|
| WidowX | cosine | 0.6364 ± 0.0751 | 0.6761 ± 0.0732 | 0.6154 ± 0.0141 |
| WidowX | Euclidean | 0.5367 ± 0.0692 | 0.6445 ± 0.0730 | 0.5492 ± 0.1104 |
| DROID | cosine | 0.4943 ± 0.0357 | 0.4919 ± 0.0254 | 0.5491 ± 0.0468 |
| DROID | Euclidean | 0.5374 ± 0.0397 | 0.5260 ± 0.0151 | 0.5530 ± 0.0423 |

校准使用已见任务成功轨迹，alpha=0.10。以下为未见任务**窗口末端**的 FPR（`at earliest stop`），与窗口内最大值的累计报警口径（`by earliest stop`）分开。

| 域 / 距离 | seed 0 | seed 1 | seed 2 |
|---|---:|---:|---:|
| WidowX / cosine | 0.0645 | 0.1803 | 0.3065 |
| WidowX / Euclidean | 0.0968 | 0.7705 | 0.5000 |
| DROID / cosine | 0.1000 | 0.1333 | 0.0556 |
| DROID / Euclidean | 0.0889 | 0.1778 | 0.0667 |

两种时序口径的原始阈值、TPR/FPR 均保存在汇总与各运行的 conformal.json；不得把末端时刻误报率写成整个运行期间的报警保证。OOD 下 alpha 不自动具有覆盖保证。

## 分析结论

简单距离型对照已补齐，形成与学习型 LSTM、MLP 的结构比较。WidowX cosine 的当前累计 AUROC 均值低于既有 MLP；DROID 两种距离仍表现较弱。这是固定配置观察，不是论文全网格最优，也未进行显著性检验。

这些基线使用既有策略特征，不包含主动外部视觉查询。后续模型必须在相同输入权限、冻结划分和计费口径下证明新增证据的价值；不能仅用另一数据域上的更高分数宣称优于它们。特征库大小、检索成本和新方法查询成本仍需统一实测。

DROID 各组另保存 `sensitivity.json`，固定训练库，仅移除评测与校准中的异常标签轨迹；这是敏感性分析，不是清洗后重建特征库。此前的训练暴露和标签异常边界继续适用。

## 复现入口与原始证据

```bash
OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 /root/autodl-tmp/conda-envs/vla-safe/bin/python scripts/eval_safe_distance_baselines.py --output /root/autodl-tmp/experiments/baselines-20260905/safe-distance-v1
/root/autodl-tmp/conda-envs/vla-safe/bin/python scripts/export_extended_baselines.py
```

输出目录已存在时，不覆盖已完成运行。完整特征库与逐时间步分数留在服务器，小型配置、划分、指标与哈希位于 [extended-baselines](results/20260905/extended-baselines/summary.json)。

来源：[SAFE 官方仓库](https://github.com/vla-safe/SAFE)。
