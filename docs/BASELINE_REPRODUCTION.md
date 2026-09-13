# Baseline report and comparison protocol

本文件与 [Baseline Report](reproduction/BASELINE_REPORT.md) 共同替换此前只记录 smoke test 的协议总览。当前成绩以该报告的五列总表为准；[PDF](reproduction/pdf/baseline_reproduction_report.pdf) 与 [LaTeX](reproduction/pdf/baseline_reproduction_report.tex) 同步维护。

报告核查日期：2026-09-13；既有实验截止：2026-09-05。本次不新增训练、采集或策略评测。

## 已有结果的使用边界

- OpenVLA-OFT / AVA-VLA：原版 LIBERO Spatial，10 任务各 5 初态，分别 50/50 和 48/50；不是论文每任务 50 次的全量结果。
- LIBERO-Plus：旧七轴子集分别 58/70 和 55/70。部分任务指令混入扰动后缀；保留为实现诊断，不回填为修正后成绩。
- SAFE：WidowX 与 DROID 两域的 LSTM、MLP、cosine、Euclidean、RND 已有固定配置、三种子结果。它们不是原论文完整网格搜索最优值。原论文没有对应 WidowX 域数值，记作 NR。
- I-FailSense：公开单视角 203 样本，完整模型 184/203、VLM 组件 174/203；accuracy 与论文 Table I 对应保留位一致。离线判断不代表在线恢复。
- WCM：公开 quick benchmark 的 18 episode、1,617 窗口；值预测误差不是论文 VLA-RL 成功率。
- ManiSkill 演示回放与 FailGen 注入：工程链路验收，不计作学习模型性能。

原始 JSON、各模型说明和旧审计均保留。指标重算入口为 `scripts/build_baseline_report.py`，仅使用 Python 标准库；输出 [五列表及输入 SHA-256](reproduction/baseline_table.json)、Markdown 与 LaTeX。PDF 用 XeLaTeX 编译两次，需 Microsoft YaHei 与 Arial 字体或等效配置。

## 数据集定位

| 资源 | 用途 | 当前边界 |
| --- | --- | --- |
| LIBERO-Plus | 视觉/初态等扰动下的主动验证与恢复主闭环 | 代码和资产已有；无提示词混杂的冻结协议结果待运行 |
| MIKASA-Robo | 独立 ManiSkill 系仿真，历史证据与部分可观测判断 | 新选入、尚未接入；锁定 MemoryVLA 五任务协议，不套用当前 90 任务版本 |
| SAFE Pi0-FAST / DROID rollout | 真实域跨任务离线失败检测 | 已有数据和检测结果；不提供任意新视角或真实恢复反事实 |
| 标准 LIBERO | 正确性与 clean 性能保持控制 | 已有 Spatial 小样本结果；不以近满分协议作为主要提升证据 |
| SMF-CALVIN / SAFE-WidowX | 离线语义判断与跨策略诊断 | 保留已有结果，不重复计入主数据集数量 |
| RoboCasa365 | 长时序家庭操作扩展 | 非当前主线必需；未作为已完成基线 |

选型证据和 8 篇 2026 论文的逐篇核查见总报告。未饱和不等于错误一定能由主动观察解决，也不等于获得顶会级贡献。

## 固定比较规则

### 模型与 harness 分开

主闭环固定同一执行策略，比较无附加验证、固定频率/固定多视角、被动 critic 触发、预算自适应证据路由。OFT、AVA、MemoryVLA 的底座切换另行报告。当前 H1-H9 是已有执行机制编号，不表示新 harness 对照已完成。

恢复动作库、最大执行步数、查询上限及输入权限一致。RGB、历史、深度、分割和 VLA 内部特征逐项声明；状态真值仅用于标注和环境验收。记忆任务仅能检索实际记录的历史，不能查询未曾保存的过去。

### 划分与代码迭代

训练、开发、校准、测试清单冻结并保存哈希。同一任务/初态根的扰动、观察分支及恢复分支不得跨集合；不按帧随机切分。程序化决策与失败驱动代码迭代只使用训练/开发反馈，最终测试冻结代码与阈值。

既用 DROID 780 条数据不能重新宣称为未触碰测试集。标签异常、既往使用记录与清理规则单独保存。

### 成本与指标

分别记录观察类型/分辨率、历史缓存及检索、critic/工具调用、GPU 秒、端到端 p95 延迟、重规划与恢复次数。开发期代码迭代成本与部署期证据预算分开；报告成功率-成本曲线，不只选一个有利阈值。

闭环报告任务成功、失败恢复成功、误干预率与证据成本。检测报告同一正类、同一时间窗的 AUROC/AUPRC、固定误报水平下检出率、检测提前量及风险-覆盖率。总表 SAFE early-stop AUROC 基于每任务最短轨迹窗口内的最大风险分数，不等于实际提前量或恢复收益。

任务和难度在测试前固定。置信区间按任务/episode 聚类，不把同轨迹多帧当作独立样本。

## 当前完成边界

已有结果可作为起始基线和开发依据，尚不构成跨主评测组合、同预算、同输入的完整新方法对照。发布代码、加载成功和工程链路通过均不自动等同于论文指标复现。ActiveVLA 与 AVA-VLA 是不同工作；前者未获得可执行发布入口时，不能使用后者成绩替代。
