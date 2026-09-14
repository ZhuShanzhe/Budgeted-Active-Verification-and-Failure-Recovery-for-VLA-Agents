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


## Harness 含义与执行流程

Model 指执行预测的模型；harness 指组织输入、模型调用、动作执行、结果判定与记录的外围流程。H1-H9 是本报告的流程编号，不是九种论文方法，也不是九套已完成的主动验证系统。训练轮数与种子属于实验配置，不属于决策机制。

### H1：标准策略执行循环

**适用与输入：**OpenVLA-OFT / AVA-VLA，标准 LIBERO Spatial。输入为任务指令、双相机图像和机器人本体状态。

**执行流程：**读取观测 → 策略生成 8 步动作块 → 环境执行 → 获取新观测 → 重复，成功或达到步数上限时结束。本批包含 10 步稳定等待，任务执行上限为 220 步。

**输出与边界：**输出逐轨迹成功与否及执行记录。AVA 使用其发布配置的历史动作特征和注意力机制，属于模型内部能力；外层没有附加 critic、主动查询或独立恢复模块。策略自行纠偏不等于外加恢复系统。

**研究位置：**无附加验证的执行策略对照。两种发布权重训练范围不同，当前差异不能全部归因于注意力机制。

### H2：扰动环境中的策略执行

**适用与输入：**OpenVLA-OFT / AVA-VLA，LIBERO-Plus Spatial 子集。两策略使用同一评测名单，输入权限与 H1 同类。

**执行流程：**选定扰动任务与初态 → 运行标准策略循环 → 环境判定结果 → 按扰动维度汇总。相机、布局、光照、语言、纹理、初态和传感器噪声七轴各 10 次。

**输出与边界：**输出扰动下成功率；没有增加异常检测、主动观察或恢复决策。旧运行部分指令混入扰动名称，成绩仅作实现诊断。

**研究位置：**H1 的扰动评测版本，不是另一种主动 harness。正式 OOD 对照使用消除非目标提示词混杂的冻结协议；语言扰动本身与意外后缀分开处理。

### H3：学习型被动失败监测

**适用与输入：**SAFE-MLP / SAFE-LSTM；分别使用 WidowX 与 DROID 已记录的 VLA 内部特征及轨迹标签，需要白盒特征访问。

**执行流程：**按任务划分数据 → 固定配置训练检测器 → 读取测试轨迹特征并输出逐时刻风险 → 汇总评分 → 使用独立校准数据确定报警阈值。MLP 映射特征，LSTM 利用时序信息。

**输出与边界：**三种子、每种子 1,000 epoch。仅离线评分与校准，不改变机器人动作；总表采用统一窗口内最大风险的 AUROC/AUPRC，不表示检测提前量或恢复收益。OOD 下校准目标不自动成为误报保证。

**研究位置：**已有证据上的被动风险检测对照；不判断缺少哪类证据，也不主动调用外部视觉工具。

### H4：基于特征检索的被动监测

**适用与输入：**SAFE 官方 Cosine / Euclidean kNN；数据、任务划分与 H3 相同，两域分别建立特征库。

**执行流程：**用训练轨迹有效时间步建立成功库和失败库 → 查询特征分别检索 k=5 近邻 → 以到成功库的距离减去到失败库的距离构造风险 → 评分与阈值校准。

**输出与边界：**两者仅距离度量不同，无梯度训练；特征库显式保存并重新加载验证。检索仍有存储与计算成本，不能把无需训练写成零成本。测试数据不参与建库。

**研究位置：**简单、可解释的风险对照。未见任务可能只是远离训练特征，并非执行失败；该机制不获取新的视觉证据。

### H5：预测误差式被动监测

**适用与输入：**SAFE 官方 RND；使用与 H3 相同的策略特征、轨迹筛选和任务划分。

**执行流程：**特征进入固定随机目标网络与可训练预测网络 → 按官方损失训练 → 根据预测误差构造风险 → 逐轨迹评分与校准。当前配置中成功和失败均参与训练，不是仅用成功数据的普通异常检测。

**输出与边界：**三种子、每种子 200 epoch；小尾批并入前批以避免原损失的数值异常，不丢弃轨迹。当前固定配置的检测排序较弱，不代表完整调参后的能力上限。

**研究位置：**另一类被动风险信号。陌生程度不等于失败程度；没有主动查询、动作干预或恢复执行。

### H6：视觉语义失败判断

**适用与输入：**I-FailSense；单视角时序拼图与任务文本。固定公开底座、LoRA 和分类器权重，在作者 validation 派生的同一批 203 样本上评测，不重新训练。

**执行流程：**完整模型：图文输入 → VLM 特征与解码判断 → 三路分类器与 VLM 加权投票 → 成功/失败。组件对照：相同图文输入 → LoRA/VLM 单 token 解码 → 按作者规则映射标签，不调用完整分类器组合。

**输出与边界：**输出逐样本判断与 accuracy；完整模型票数比例不是校准概率。该批数据不是自行冻结的全新 OOD 测试集，离线识别也不等于在线恢复。

**研究位置：**任务条件视觉验证工具的参考。输入证据预先固定，没有主动换视角、证据预算分配或恢复闭环。

### H7：固定历史窗口预测

**适用与输入：**WCM 官方 pick-place quick benchmark 与公开检查点；18 个 episode、1,617 个历史时序窗口。

**执行流程：**按官方验证划分构造窗口 → 固定 WCM 前向预测价值与下一状态 → 与数据目标比较 → 汇总预测误差和相关性。

**输出与边界：**报告价值 RMSE、MAE、Pearson 和下一状态 MSE。没有执行完整 VLA-RL 控制闭环；公开 quick benchmark 只含成功轨迹，不能单独证明失败检测或恢复能力。

**研究位置：**部分可观测条件下的历史表征参考。固定窗口不会决定何时检索历史、选择哪些证据或何时停止查询。

### H8：官方演示动作回放

**适用与输入：**ManiSkill3 的 PickCube、StackCube、PegInsertionSide，各 3 条官方演示；输入为演示初态和动作序列。

**执行流程：**加载演示与初态 → 在仿真中执行记录动作 → 读取环境终局判定 → 汇总回放结果。执行动作，不逐帧强制写入演示状态。

**输出与边界：**9/9 回放成功。没有学习模型根据图像作决策，因此不是策略成功率基线，只证明选定演示、动作接口和环境执行链路可用。

**研究位置：**第二环境的数据采集与执行接口验收，不与新模型的性能直接排名。

### H9：程序化扰动与结果标注

**适用与输入：**ManiSkill-FailGen；PickCube / StackCube，grasp / trans_x 两类扰动，种子 7/8，共 8 次运行。

**执行流程：**选定任务与扰动配置 → 注入抓取或平移扰动并继续执行 → 读取环境实际结果 → 保存生成图像及成功/失败记录。扰动注入本身不作为失败标签。

**输出与边界：**8/8 链路完成，其中 4 成功、4 失败。当前上游入口主要保存多视角拼接帧，未构成含完整时序、动作、证据成本和恢复分支的正式训练数据集；不是 AHA critic 的准确率。

**研究位置：**可控失败案例生成工具。用于后续数据管线扩展，不是失败检测模型或已经完成的恢复系统。


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
