# Baseline Report


## Baseline 五列总表

| dataset | model | harness | reported performance(in paper) | our reproduced performance |
| --- | --- | --- | --- | --- |
| LIBERO<br>Spatial | OpenVLA-OFT | H1：作者策略循环；双相机＋本体；10 任务×5 初态；无外加验证/恢复。 | SR 97.6%；Spatial 专用策略。[1](https://arxiv.org/html/2502.19645) | SR 100.00%（50/50）；每任务 5 次，不是论文 50 次。 |
| LIBERO<br>Spatial | AVA-VLA | H1：作者策略循环；双相机＋本体；10 任务×5 初态；无外加验证/恢复。 | SR 97.4%；四套件联合策略。[2](https://openaccess.thecvf.com/content/CVPR2026/papers/Xiao_AVA-VLA_Improving_Vision-Language-Action_models_with_Active_Visual_Attention_CVPR_2026_paper.pdf) | SR 96.00%（48/50）；每任务 5 次，不是论文 50 次。 |
| LIBERO-Plus<br>Spatial 子集 | OpenVLA-OFT | H2：七轴各 10 次；两策略同名单；保留上游提示词混杂。 | 全套件 SR 69.6%；仅作背景参照，非本批 Spatial 子集。[3](https://arxiv.org/pdf/2510.13626) | SR 82.86%（58/70）；诊断值，不作论文优劣比较。 |
| LIBERO-Plus<br>Spatial 子集 | AVA-VLA | H2：七轴各 10 次；两策略同名单；保留上游提示词混杂。 | NR：AVA 论文未报告本批 Plus 协议。[2](https://openaccess.thecvf.com/content/CVPR2026/papers/Xiao_AVA-VLA_Improving_Vision-Language-Action_models_with_Active_Visual_Attention_CVPR_2026_paper.pdf) | SR 78.57%（55/70）；诊断值，不作论文优劣比较。 |
| SAFE rollout<br>OpenVLA / WidowX | SAFE-LSTM | H3：白盒特征；3 种子；1,000 epoch；按任务划分；仅评分/校准，不干预。 | NR：原论文未列出 WidowX 域数值。[4](https://arxiv.org/html/2506.09937v2) | 未见任务 AUROC 62.78 ± 0.99；AUPRC 73.98 ± 2.30。 |
| SAFE rollout<br>OpenVLA / WidowX | SAFE-MLP | H3：白盒特征；3 种子；1,000 epoch；按任务划分；仅评分/校准，不干预。 | NR：原论文未列出 WidowX 域数值。[4](https://arxiv.org/html/2506.09937v2) | 未见任务 AUROC 81.85 ± 3.67；AUPRC 87.34 ± 3.84。 |
| SAFE rollout<br>OpenVLA / WidowX | Cosine kNN | H4：同 H3 划分；固定 k=5；训练轨迹建库，无梯度训练。 | NR：原论文未列出 WidowX 域数值。[4](https://arxiv.org/html/2506.09937v2) | 未见任务 AUROC 63.64 ± 7.51；AUPRC 67.61 ± 7.32。 |
| SAFE rollout<br>OpenVLA / WidowX | Euclidean kNN | H4：同 H3 划分；固定 k=5；训练轨迹建库，无梯度训练。 | NR：原论文未列出 WidowX 域数值。[4](https://arxiv.org/html/2506.09937v2) | 未见任务 AUROC 53.67 ± 6.92；AUPRC 64.45 ± 7.30。 |
| SAFE rollout<br>OpenVLA / WidowX | RND | H5：同划分；3 种子×200 epoch；小尾批合并；仅检测，无恢复。 | NR：原论文未列出 WidowX 域数值。[4](https://arxiv.org/html/2506.09937v2) | 未见任务 AUROC 49.41 ± 4.01；AUPRC 59.56 ± 4.96。 |
| SAFE rollout<br>Pi0-FAST / DROID | SAFE-LSTM | H3：白盒特征；3 种子；1,000 epoch；按任务划分；仅评分/校准，不干预。 | 未见任务 AUROC 58.70 ± 4.37；Real Franka 列，论文调优配置。[4](https://arxiv.org/html/2506.09937v2) | 未见任务 AUROC 53.58 ± 2.08；AUPRC 53.93 ± 4.75。 |
| SAFE rollout<br>Pi0-FAST / DROID | SAFE-MLP | H3：白盒特征；3 种子；1,000 epoch；按任务划分；仅评分/校准，不干预。 | 未见任务 AUROC 64.16 ± 5.88；Real Franka 列，论文调优配置。[4](https://arxiv.org/html/2506.09937v2) | 未见任务 AUROC 53.53 ± 4.45；AUPRC 61.34 ± 3.01。 |
| SAFE rollout<br>Pi0-FAST / DROID | Cosine kNN | H4：同 H3 划分；固定 k=5；训练轨迹建库，无梯度训练。 | 未见任务 AUROC 59.51 ± 5.76；Real Franka 列，论文调优配置。[4](https://arxiv.org/html/2506.09937v2) | 未见任务 AUROC 49.43 ± 3.57；AUPRC 49.19 ± 2.54。 |
| SAFE rollout<br>Pi0-FAST / DROID | Euclidean kNN | H4：同 H3 划分；固定 k=5；训练轨迹建库，无梯度训练。 | 未见任务 AUROC 60.27 ± 4.79；Real Franka 列，论文调优配置。[4](https://arxiv.org/html/2506.09937v2) | 未见任务 AUROC 53.74 ± 3.97；AUPRC 52.60 ± 1.51。 |
| SAFE rollout<br>Pi0-FAST / DROID | RND | H5：同划分；3 种子×200 epoch；小尾批合并；仅检测，无恢复。 | 未见任务 AUROC 45.83 ± 5.10；Real Franka 列，论文调优配置。[4](https://arxiv.org/html/2506.09937v2) | 未见任务 AUROC 48.87 ± 1.96；AUPRC 49.38 ± 0.98。 |
| SMF-CALVIN<br>公开 1p 数据 | I-FailSense<br>完整模型 | H6：单视角时序拼图＋文本；203 样本；固定发布权重；离线投票/解码。 | 1p accuracy 90.64%；Table I。[5](https://arxiv.org/html/2509.16072v1) | Accuracy 90.64%（184/203）；与论文保留位一致。 |
| SMF-CALVIN<br>公开 1p 数据 | I-FailSense<br>LoRA/VLM 组件 | H6：单视角时序拼图＋文本；203 样本；固定发布权重；离线投票/解码。 | 1p accuracy 85.71%；Table I。[5](https://arxiv.org/html/2509.16072v1) | Accuracy 85.71%（174/203）；与论文保留位一致。 |
| WCM<br>pick-place val | WCM | H7：固定公开权重；18 episode / 1,617 窗口；值与下一状态预测。 | NR：未定位同一 quick-val 的误差报告；论文 RL 成功率不可替代。[6](https://github.com/sylvestf/WCM) | Value RMSE 0.380342；MAE 0.196550；Pearson 0.720664；next-state MSE 0.007358。 |
| ManiSkill3<br>三任务 | 官方演示<br>动作回放 | H8：PickCube、StackCube、PegInsertionSide 各 3 条；执行动作，不逐帧写真值。 | N/A：工程回放，不是学习策略论文指标。 | 9/9 回放成功；只说明演示可执行。 |
| ManiSkill3<br>两任务 | FailGen<br>失败注入器 | H9：grasp / trans_x；seed 7/8；按环境终局判定，不把注入直接当失败。 | N/A：不是 AHA 检测准确率。 | 8/8 链路完成；4 成功、4 失败。 |

SR / accuracy 用百分数；AUROC / AUPRC 用 0-100 尺度。本次 SAFE 为三种子均值±样本标准差，采用每任务最短轨迹窗口内最大风险分数；不代表实际检测提前量。

NR：论文未给出对应域/协议值；N/A：非模型性能。两列并排不等于同协议比较；样本量、调优范围和 Plus 旧提示词混杂已在表内标明。


## 有提升空间的数据集

以下为特定版本与协议下的性能证据，不是全社区最新排名；剩余失败也不一定都可由主动观察解决。标准 LIBERO 仅保留为干净控制项，不作为主要提升空间。

### LIBERO-Plus：扰动下的主动验证与恢复

作者报告 OFT 全套件 SR 69.6%，其中相机扰动 56.4%、初态扰动 31.9%；mix-SFT 整体 79.5%，仍有提升空间。[3](https://arxiv.org/pdf/2510.13626) 本研究用于视觉/初态等分布变化下的证据获取与失败恢复。代码和资产已有；现有 70 次结果含提示词混杂，仅作诊断，正式比较须使用冻结的无混杂协议。

### MIKASA-Robo：历史证据与部分可观测判断

MemoryVLA 论文五任务协议中，OFT SR 28.4%、MemoryVLA 41.2%。[7](https://arxiv.org/html/2508.19236v2) 该协议包括 ShellGameTouch、InterceptMedium、RememberColor3/5/9，适合检验历史检索和证据不足判断。环境与数据公开，但本项目尚未接入或复现；不能将旧五任务成绩套到当前 90 任务版本。[8](https://github.com/CognitiveAISystems/MIKASA-Robo) 模型只能查询真实保存的历史，不获取未记录的过去或状态真值。

### SAFE Pi0-FAST / DROID：真实跨任务失败检测

论文 Real Franka 列中 MLP 的未见任务 AUROC 为 64.16，本次固定配置为 53.53；该差距含调优协议差异，不能直接视作新方法可获得的增益。[4](https://arxiv.org/html/2506.09937v2) 已有 1,464 条原始 rollout、780 条既用筛选数据，可用于真实域离线验证。它不是 DROID 全集，也不提供交互式新视角或真实恢复反事实；标签异常与既往数据使用须保留记录。

### RoboCasa365：长时序家庭操作扩展

论文 Table 2 的 GR00T N1.5 在预训练＋目标全数据微调设置下，atomic SR 68.5%、composite-seen 40.6%、composite-unseen 42.1%。[9](https://arxiv.org/html/2603.04356) 复合任务仍有明显空间，适合环境反馈与阶段性恢复。该数据集作为扩展项，尚未完成本项目基线；控制适配与长时序采集成本较高，不与旧版 RoboCasa 成绩混用。
