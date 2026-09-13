"""Build the baseline report from audited results; never run or modify experiments.

Usage: python scripts/build_baseline_report.py
Then compile docs/reproduction/pdf/baseline_reproduction_report.tex with XeLaTeX twice.
"""
from pathlib import Path
import hashlib
import json
import re
import statistics

ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / 'docs/reproduction'
PDF = DOC / 'pdf'
EVIDENCE = {}


def read_result(relative):
    # Local historical export fallback; the published repository has canonical results/.
    candidates = [DOC / relative, ROOT.parent / 'outputs/baseline-results-20260905/docs/reproduction' / relative]
    path = next((p for p in candidates if p.exists()), None)
    if path is None:
        raise FileNotFoundError(relative)
    data = path.read_bytes()
    EVIDENCE[relative] = hashlib.sha256(data).hexdigest()
    return json.loads(data)


SOURCES = [
 ('OFT', 'OpenVLA-OFT：原论文 Table I（2025）', 'https://arxiv.org/html/2502.19645'),
 ('AVA', 'AVA-VLA：CVPR 2026，Table 1、Table 2 与真机实验', 'https://openaccess.thecvf.com/content/CVPR2026/papers/Xiao_AVA-VLA_Improving_Vision-Language-Action_models_with_Active_Visual_Attention_CVPR_2026_paper.pdf'),
 ('PLUS', 'LIBERO-Plus：CVPR 2026；原论文结果表', 'https://openaccess.thecvf.com/content/CVPR2026/html/Fei_LIBERO-Plus_A_Progressive_Robustness_Benchmark_for_Visual-Language-Action_Models_CVPR_2026_paper.html'),
 ('PLUSNUM', 'LIBERO-Plus：作者论文完整表与各套件明细', 'https://arxiv.org/pdf/2510.13626'),
 ('SAFE', 'SAFE：NeurIPS 2025，Table 8、B.8 与真实 Franka 实验', 'https://arxiv.org/html/2506.09937v2'),
 ('IFS', 'I-FailSense：Table I 与评测定义', 'https://arxiv.org/html/2509.16072v1'),
 ('WCM', 'WCM：作者公开 quick benchmark、数据与权重', 'https://github.com/sylvestf/WCM'),
 ('MEM', 'MemoryVLA：ICLR 2026；4.1-4.5，Table 4', 'https://arxiv.org/html/2508.19236v2'),
 ('MEMVENUE', 'MemoryVLA：作者 ICLR 2026 项目与公开资源', 'https://shihao1895.github.io/MemoryVLA/'),
 ('HAM', 'HAMLET：ICLR 2026；Tables 2-3、真机实验', 'https://arxiv.org/html/2510.00695'),
 ('HAMVENUE', 'HAMLET：ICLR 2026 正式会议条目', 'https://iclr.cc/virtual/2026/poster/10010110'),
 ('SP', 'SP-VLA：ICLR 2026 正式会议论文', 'https://proceedings.iclr.cc/paper_files/paper/2026/hash/4072543747a14bbed76284cf2c04b9e9-Abstract-Conference.html'),
 ('SPFULL', 'SP-VLA：实验设置与真机补充', 'https://arxiv.org/html/2506.12723'),
 ('SIMPLE', 'SimpleVLA-RL：ICLR 2026，3.1 实验设置', 'https://proceedings.iclr.cc/paper_files/paper/2026/file/cbfbcb4da14235bd69b134070898ae9d-Paper-Conference.pdf'),
 ('COSMOS', 'Cosmos Policy：ICLR 2026 正式会议条目', 'https://proceedings.iclr.cc/paper_files/paper/2026/hash/748becc400a57c0e31cfe6a2e7951467-Abstract-Conference.html'),
 ('ACTIVE', 'ActiveVLA：CVPR 2026 正式会议论文', 'https://openaccess.thecvf.com/content/CVPR2026/html/Liu_ActiveVLA_Injecting_Active_Perception_into_Vision-Language-Action_Models_for_Precise_3D_CVPR_2026_paper.html'),
 ('ACTIVEFULL', 'ActiveVLA：4.1 与三套仿真基准', 'https://arxiv.org/html/2601.08325v1'),
 ('STABLE', 'StableVLA：ICML 2026；Table 1 与真机设置', 'https://dagroup-pku.github.io/StableVLA/'),
 ('STABLEVENUE', 'ICML 2026 官方论文列表（含 StableVLA）', 'https://icml.cc/Downloads/2026'),
 ('MIKASA', 'MIKASA-Robo：官方数据、环境与版本说明', 'https://github.com/CognitiveAISystems/MIKASA-Robo'),
 ('MIKASAV', 'MIKASA-Robo：90 任务 VLA 版与旧 RL 版发布边界', 'https://github.com/CognitiveAISystems/MIKASA-Robo/releases'),
 ('ROBOCASA', 'RoboCasa365：Table 2，目标任务微调后的成功率', 'https://arxiv.org/html/2603.04356'),
 ('ACTIVECODE', 'ActiveVLA：本次核查仍待发布的代码与评测入口', 'https://github.com/ZhenyangLiu/ActiveVLA-Injecting-Active-Perception-into-VLA'),
]
SOURCE_INDEX = {key: i + 1 for i, (key, _, _) in enumerate(SOURCES)}
HEADERS = ['dataset', 'model', 'harness', 'reported performance(in paper)', 'our reproduced performance']


def avg_sd(values):
    assert len(values) == 3
    return f'{100 * statistics.mean(values):.2f} ± {100 * statistics.stdev(values):.2f}'


def baseline_rows():
    rows = []
    def add(group, dataset, model, harness, reported, ours, evidence):
        rows.append(dict(group=group, dataset=dataset, model=model, harness=harness,
                         reported=reported, ours=ours, evidence=evidence))
    for policy, name, reported in [
        ('oft', 'OpenVLA-OFT', 'SR 97.6%；Spatial 专用策略。[OFT]'),
        ('ava', 'AVA-VLA', 'SR 97.4%；四套件联合策略。[AVA]')]:
        rel = f'results/20260905/{policy}-clean-spatial-50/summary.json'
        s = read_result(rel)
        add('A. 策略闭环：有限规模', 'LIBERO\nSpatial', name,
            'H1：作者策略循环；双相机＋本体；10 任务×5 初态；无外加验证/恢复。',
            reported, f"SR {s['success_rate']*100:.2f}%（{s['successes']}/{s['episodes']}）；每任务 5 次，不是论文 50 次。", rel)
    for policy, name in [('oft', 'OpenVLA-OFT'), ('ava', 'AVA-VLA')]:
        rel = f'results/20260905/{policy}-plus-spatial-70/summary.json'
        s = read_result(rel)
        reported = ('全套件 SR 69.6%；仅作背景参照，非本批 Spatial 子集。[PLUSNUM]' if policy == 'oft'
                    else 'NR：AVA 论文未报告本批 Plus 协议。[AVA]')
        add('B. OOD：旧实现诊断，不进入主结果', 'LIBERO-Plus\nSpatial 子集', name,
            'H2：七轴各 10 次；两策略同名单；保留上游提示词混杂。', reported,
            f"SR {s['success_rate']*100:.2f}%（{s['successes']}/{s['episodes']}）；诊断值，不作论文优劣比较。", rel)
    for domain, summary in [('widowx', 'results/20260905/safe_summary.json'),
                            ('droid', 'results/20260905/safe-droid-v1/summary.json')]:
        d = read_result(summary)
        for model, name, pub in [('lstm', 'SAFE-LSTM', '58.70 ± 4.37'), ('indep', 'SAFE-MLP', '64.16 ± 5.88')]:
            runs = [r for r in d['runs'] if r['model'] == model]
            auc = avg_sd([r['metrics']['falert_early_roc_auc/model_val_unseen'] for r in runs])
            pr = avg_sd([r['metrics']['falert_early_prc_auc/model_val_unseen'] for r in runs])
            add('C. 失败检测：固定配置，未见任务',
                'SAFE rollout\n'+('OpenVLA / WidowX' if domain == 'widowx' else 'Pi0-FAST / DROID'), name,
                'H3：白盒特征；3 种子；1,000 epoch；按任务划分；仅评分/校准，不干预。',
                'NR：原论文未列出 WidowX 域数值。[SAFE]' if domain == 'widowx' else f'未见任务 AUROC {pub}；Real Franka 列，论文调优配置。[SAFE]',
                f'未见任务 AUROC {auc}；AUPRC {pr}。', summary)
        for method, name, pub in [('cosine', 'Cosine kNN', '59.51 ± 5.76'), ('euclid', 'Euclidean kNN', '60.27 ± 4.79'), ('rnd', 'RND', '45.83 ± 5.10')]:
            rel = 'results/20260905/safe-rnd-v1/summary.json' if method == 'rnd' else 'results/20260905/extended-baselines/summary.json'
            d2 = read_result(rel)
            runs = [r for r in d2['runs'] if r['domain'] == domain and (method == 'rnd' or r['method'] == method)]
            auc = avg_sd([r['metrics']['falert_early_roc_auc/model_val_unseen'] for r in runs])
            pr = avg_sd([r['metrics']['falert_early_prc_auc/model_val_unseen'] for r in runs])
            add('C. 失败检测：固定配置，未见任务',
                'SAFE rollout\n'+('OpenVLA / WidowX' if domain == 'widowx' else 'Pi0-FAST / DROID'), name,
                ('H4：同 H3 划分；固定 k=5；训练轨迹建库，无梯度训练。' if method != 'rnd' else
                 'H5：同划分；3 种子×200 epoch；小尾批合并；仅检测，无恢复。'),
                'NR：原论文未列出 WidowX 域数值。[SAFE]' if domain == 'widowx' else f'未见任务 AUROC {pub}；Real Franka 列，论文调优配置。[SAFE]',
                f'未见任务 AUROC {auc}；AUPRC {pr}。', rel)
    for folder, name, pub in [('ifailsense-calvin1p-v1', 'I-FailSense\n完整模型', '90.64'),
                               ('ifailsense-vlm-component-v1', 'I-FailSense\nLoRA/VLM 组件', '85.71')]:
        rel = f'results/20260905/{folder}/metrics.json'
        d = read_result(rel)
        accuracy = d['accuracy'] if 'accuracy' in d else d['accuracy_abstentions_incorrect']
        correct = round(accuracy * d['samples'])
        add('D. 图像/时序拼图判断：作者派生测试集', 'SMF-CALVIN\n公开 1p 数据', name,
            'H6：单视角时序拼图＋文本；203 样本；固定发布权重；离线投票/解码。',
            f'1p accuracy {pub}%；Table I。[IFS]',
            f"Accuracy {100*accuracy:.2f}%（{correct}/{d['samples']}）；与论文保留位一致。", rel)
    rel = 'results/WCM/summary.json'
    d = read_result(rel); m = d['metrics']
    add('E. 世界模型：公开小型验证协议', 'WCM\npick-place val', 'WCM',
        'H7：固定公开权重；18 episode / 1,617 窗口；值与下一状态预测。',
        'NR：未定位同一 quick-val 的误差报告；论文 RL 成功率不可替代。[WCM]',
        f"Value RMSE {m['value_rmse']:.6f}；MAE {m['value_mae']:.6f}；Pearson {m['value_pearson']:.6f}；next-state MSE {m['next_state_mse']:.6f}。", rel)
    rel = 'results/20260905/maniskill_replay_summary.json'
    replay = read_result(rel)
    episodes = [e for task in replay for e in task['episodes']]
    successes = sum(e['success'] for e in episodes)
    assert len(replay) == 3 and len(episodes) == 9
    add('F. 数据生成与环境检查：不是模型性能', 'ManiSkill3\n三任务', '官方演示\n动作回放',
        'H8：PickCube、StackCube、PegInsertionSide 各 3 条；执行动作，不逐帧写真值。',
        'N/A：工程回放，不是学习策略论文指标。', f'{successes}/{len(episodes)} 回放成功；只说明演示可执行。', rel)
    rel = 'results/20260905/failgen-smoke/summary.json'
    d = read_result(rel)
    good = sum(r['task_success'] for r in d)
    add('F. 数据生成与环境检查：不是模型性能', 'ManiSkill3\n两任务', 'FailGen\n失败注入器',
        'H9：grasp / trans_x；seed 7/8；按环境终局判定，不把注入直接当失败。',
        'N/A：不是 AHA 检测准确率。', f'{len(d)}/8 链路完成；{good} 成功、{len(d)-good} 失败。', rel)
    assert len(rows) == 19
    return rows


SAMPLE = [
 ['HAMLET [HAM][HAMVENUE]', 'ICLR 2026', 'LIBERO；RoboCasa Kitchen；SimplerEnv', '3', '有；跨基准迁移，不只摘要中的两套'],
 ['MemoryVLA [MEM][MEMVENUE]', 'ICLR 2026', 'LIBERO；SimplerEnv；MIKASA-Robo', '3', '有；Bridge/Fractal 合并，不把真机两类任务拆算'],
 ['SP-VLA [SP][SPFULL]', 'ICLR 2026', 'LIBERO；SimplerEnv', '2', '有；效率与任务质量同时评测'],
 ['SimpleVLA-RL [SIMPLE]', 'ICLR 2026', 'LIBERO；RoboTwin 1.0 / 2.0', '2', '有；若版本分开，原文计 3'],
 ['Cosmos Policy [COSMOS]', 'ICLR 2026', 'LIBERO；RoboCasa', '2', '有；RoboCasa 不是 RoboCasa365'],
 ['AVA-VLA [AVA]', 'CVPR 2026', 'LIBERO；CALVIN', '2', '有；四个 LIBERO 套件只计 1'],
 ['ActiveVLA [ACTIVE][ACTIVEFULL]', 'CVPR 2026', 'RLBench；COLOSSEUM；GemBench', '3', '有；三者共享 RLBench 系仿真底座'],
 ['StableVLA [STABLE][STABLEVENUE]', 'ICML 2026', 'LIBERO；CALVIN', '2', '有；多个扰动等级不增加数据集数'],
]

INTRO = [
 '本报告以一张五列总表汇总既有实验，并据 2026 年相关顶会论文确定后续评测覆盖范围。实验记录截至 2026-09-05，文献及报告核查截至 2026-09-13；本次不新增训练、策略评测或数据采集。',
 '核心判断：标准 LIBERO 作为正确性与性能保持对照，不承担主要提升证据；LIBERO-Plus 承担扰动下的主动验证与恢复；MIKASA-Robo 的记忆任务承担独立仿真的时序证据评测；SAFE-DROID 承担真实轨迹上的外部失败检测。MIKASA-Robo 是本次选出的待接入评测，不是已经复现完成的数据集。',
 '“2026 顶会大多需要三个数据集”没有得到本次样本支持。8 篇相关主会论文在统一口径下使用 2-3 个仿真 benchmark：5 篇为 2 个、3 篇为 3 个，并各有真机实验。该小规模定向核查不是全年论文普查，更不是投稿硬性要求。',
 'harness 在本报告中指模型外部的执行与评测机制：输入封装、历史管理、工具调用、阈值、动作循环、恢复及成本记账。模型本身的记忆或注意力不等于外部主动证据获取。当前实验中没有已完成的“预算路由＋代码迭代”新方法成绩。',
]

RULES = [
 'SR 与 accuracy 用百分数；AUROC / AUPRC 用 0-100 尺度，不是任务成功率。本次 SAFE 的 ± 为 3 种子均值与样本标准差，论文 ± 沿用原文；WCM 保留原始尺度。SAFE 主表取 early-stop 窗口内最大风险分数，成败轨迹均截到每任务最短轨迹长度；该指标不等于实际检测提前量或恢复收益。',
 'NR 表示未在核查论文中定位到对应数据域/协议的报告值；N/A 表示该行根本不是论文模型性能指标。缺项不填 0，不从柱状图目测编造精确值。',
 '左右两列并排用于追溯，不自动表示公平的同协议复现：OFT/AVA 的试验规模不同；SAFE 的超参数搜索范围不同；Plus 的旧诊断协议存在提示词混杂。所有这些差异在 harness 与复现列中显式披露。',
]

FINDINGS = [
 ('固定策略与提升空间', 'OFT 50/50、AVA 48/50 来自同一组小样本 Spatial 初态，不能据此宣称超过论文，也不能用这一接近满分的协议作为新方法主要卖点。正式对照冻结同一执行策略；比较不加 harness、固定查询、轻量风险触发与预算自适应查询，保持底座、输入权限和恢复动作库一致。'),
 ('LIBERO-Plus 的旧分数不回填成修正后成绩', 'OFT 58/70、AVA 55/70 是有效的执行诊断，但上游把扰动后缀混入部分非语言任务指令。两列分数不能与全量论文分数直接相减。正式协议对非语言轴固定标准任务文本，按预注册名单重新运行；旧证据保持原样。'),
 ('SAFE：区分调优缺口与研究缺口', 'DROID 上论文 Real Franka 列的 MLP AUROC 为 64.16，本次固定配置为 53.53；这不是证明原方法失效，也不能把补齐基线调优当作新方法贡献。WidowX 未在原论文表中给出对应值。已有真实域结果支持继续研究跨任务判断，但 DROID 标签异常、特征选择与校准稳定性仍需在开发/校准划分中处理。[SAFE]'),
 ('I-FailSense：对应成绩吻合，结论范围有限', '单视角完整模型 accuracy 90.64%，组件 85.71%，均与论文 Table I 的保留位一致。已有固定权重和作者派生划分使其成为最接近论文对应条目的复现。该结果不是未触碰 OOD 保证，也不含可交互换视角或恢复；论文的 success-F1 与我们记录的 failure-F1 不直接比较。[IFS]'),
 ('WCM 与数据生成不混排', 'WCM 公开验证集只含成功轨迹，值误差不能说明失败识别能力。9/9 演示回放和 FailGen 的 8 次注入用于工程验收，不能证明 ManiSkill3 已饱和、AHA 检测有效或主动恢复成功。'),
 ('与本研究的区别', '已有实验覆盖固定执行策略、被动风险检测、离线视觉判断与短时序预测。新增研究对象是“何时缺证据、查询什么、何时停止或恢复”，并由受约束程序执行决策。代码迭代仅使用训练/开发失败案例；测试反馈不进入代码修改循环。当前报告中的空白属于尚待验证的能力，不是已经获得的增益。'),
]

COUNTING = [
 '纳入范围：与本研究直接相关的记忆、主动感知、鲁棒性、效率及策略改进方法，覆盖 ICLR、ICML、CVPR 2026 主会。只收录有正式会议条目或官方接收信息且能核对实验设置的 8 篇。SAFE 属于 NeurIPS 2025；WCM 属于 2026 预印本参考，二者不进入这个计数样本。',
 '统一规则：只计用于机器人任务结果评测的命名仿真 benchmark；训练语料不计。LIBERO 四/五套件合并，SimplerEnv 的 Bridge/Fractal 合并，RoboTwin 1.0/2.0 合并；有独立任务/划分的派生 benchmark 单列，但不等同于独立仿真平台。真机实验单列，不能叫作第三个公开数据集。',
 '统一计数均值 2.375、中位数 2，8/8 落在 2-3 之间。若将 RoboTwin 两版本分开，变为 4 篇用 2 个、4 篇用 3 个，仍不能推出“大多数恰好 3 个”。MemoryVLA 原文把部分协议及真机类别细分为 6 个 benchmark，也不等于 6 个独立数据集。[MEM][SIMPLE]',
 '结论不是凑齐三套数据，而是覆盖不同失效机制，并有跨平台或真实域证据。没有实体机器人时，真实离线数据能够补充域外检测证据，但不能替代真机主动观察与恢复实验。本文研究结论将限定在已实际验证的范围。',
]

DATASETS = [
 ['LIBERO 标准套件', 'OFT 四套件均值 97.1%；AVA 联合策略 98.0%；Cosmos Policy 98.5%。[OFT][AVA][COSMOS]', '接近上限：保留控制项，不以 clean SR 单独证明创新。', '已有 Spatial 两策略结果；其他套件不是本次全量复现。'],
 ['LIBERO-Plus', '作者 OFT 全套件 69.6%；相机 56.4%、初态 31.9%；作者 mix-SFT 整体 79.5%。[PLUSNUM]', '选入：视觉/初态扰动、证据不足与恢复主闭环。', '代码、资产与采集接口已有；正式无提示词混杂结果待运行。'],
 ['MIKASA-Robo\nMemoryVLA 五任务协议', '同表 OFT 28.4%、MemoryVLA 41.2%；记忆相关任务仍有明显空间。[MEM]', '选入：独立 ManiSkill 系平台；评测历史证据检索与部分可观测验证。', '已有 ManiSkill 基础，不等于 MIKASA 已安装/复现；需锁定旧协议、数据与权重。'],
 ['SAFE Pi0-FAST / DROID', '论文最佳所列 MLP 未见任务 AUROC 64.16；本次固定配置 53.53。[SAFE]', '选入：真实域外部离线失败检测；不是 DROID 全集。', '已有 1,464 条原始 rollout、780 条既用筛选数据；标签审计已有。'],
 ['RoboCasa365', 'GR00T N1.5 预训练＋目标全数据微调：atomic 68.5%、composite-seen 40.6%、composite-unseen 42.1%。[ROBOCASA]', '保留扩展：明确未接近满分，但控制适配与长时序成本更高。', '未作为已完成基线；不把旧 RoboCasa 的 67.1% 当作 365 版成绩。'],
 ['SMF-CALVIN / SAFE-WidowX', 'I-FailSense accuracy 90.64%；WidowX 本次 MLP AUROC 81.85。[IFS]', '保留诊断：语义判断、跨策略检测；不额外重复凑主数据集数量。', '已完成相应离线基线；不能据此证明交互式工具路由。'],
]

SELECTION = [
 '主评测组合确定为“两套仿真基准＋一套真实离线数据”：LIBERO-Plus、MIKASA-Robo、SAFE-DROID；标准 LIBERO 是干净控制项。它覆盖视觉扰动、时序记忆和真实跨任务三种问题，而不是把三个指标不同的分数平均成一个总分。',
 'MIKASA 接入采用 MemoryVLA 论文的五任务协议：ShellGameTouch、InterceptMedium、RememberColor3/5/9。论文设置为每任务 250 演示、100 评测 episode、128×128 图像；当前官方仓库已存在 90 任务 VLA 版本，不能将 41.2% 移植成新版本成绩。环境提交、任务 ID、控制器与数据版本一致后才进入数值主表。[MEM][MIKASA][MIKASAV]',
 'MIKASA 的环境和数据公开，能够复用 ManiSkill 的工程经验，但发布策略/控制适配及状态分叉仍需验收。此项是新的研发接入工作，不是零成本增加第三套数据。仅下载固定五任务所需资源，不默认获取整个新版本数据；底层 privileged state 只供标签和验收，不开放给模型。',
 '历史证据与新观察必须分开：记忆任务中未曾记录的过去画面不能事后“购买”，当前多拍一帧也不一定恢复被遮挡的历史事实。harness 只能检索真实已记录历史，且所有对照遵循相同的缓存、保留和检索成本规则。',
 'SAFE-DROID 只证明真实数据上的检测迁移。既有轨迹不能生成任意视角的物理反事实或真实恢复成功标签；已用 780 条也不能再称作全新未触碰测试。标签异常清理、任务划分与数据使用历史全部显式记录。',
 'RoboCasa365 作为长时序家庭场景扩展，不在当前主线同时增加移动底盘、全套 365 任务或完整大模型重训。其微调后约 40% 的复合任务成绩比接近零分的零样本任务更适合区分验证/恢复能力与底层策略根本不会执行的情况。[ROBOCASA]',
]

PROTOCOL = [
 ('同底座、同权限', '主闭环固定执行策略。OFT、AVA、MemoryVLA 的换底座比较与同底座加 harness 比较分开。RGB、历史、深度、分割、内部特征分别标注权限；禁止把获得额外特权输入的收益写成路由本身的提升。'),
 ('固定可比较的 harness', '主对照包含：无附加验证、固定频率/固定多视角、被动 critic 触发、预算自适应证据路由。恢复库、最大动作步数与预算上限一致；增加程序迭代模块时，以同一冻结初始版本作对照，报告迭代调用与执行成本。现有 H1-H9 不等于这些对照已完成。'),
 ('按任务根隔离', '先固定训练、开发、校准、测试清单及哈希。相同初态根的扰动、观察分支与恢复分支不能跨集合。程序生成只使用开发反馈；测试时冻结代码。自演化训练预算与部署期查询预算分开记账。'),
 ('报告真正相关的结果', '闭环按数据集分别报告任务 SR、失败恢复 SR、误干预率、证据调用数、GPU 秒及 p95 延迟。检测使用相同时间窗、相同正类的 AUROC/AUPRC、固定误报水平下的检出率与提前量。拒判同时报告覆盖率，不把“少报警”当作“更安全”。'),
 ('难度与公平性验收', '在开发集检查失败是否可观察、可干预，排除基础设施错误与完全不可执行状态。难度和任务名单在最终测试前固定，不根据新方法优势筛选；统计区间按任务/episode 聚类，避免把同一轨迹的多帧当独立样本。'),
 ('本报告的完成边界', '已有结果足以作为起始基线与方法开发依据，但尚无跨上述主组合、同预算、同输入的完整新方法对照。数据集尚未饱和不意味着一定存在可由主动观察解决的剩余错误，更不意味着已获得顶会级贡献。'),
]

TRACE = [
 '表中所有 our reproduced performance 来自仓库已有结果，不来自论文或新模拟数字。生成脚本从原始汇总 JSON 重算 SAFE 均值/样本标准差，并保存每个输入文件 SHA-256 与表行对应关系。',
 'H1/H2 的详细协议见 OPENVLA_AVA_VLA.md、LIBERO_PLUS.md；H3-H5 见 SAFE_20260905.md、SAFE_DROID_20260905.md、EXTENDED_BASELINES_20260905.md、SAFE_RND_20260905.md；H6-H9 见 IFAILSENSE_20260905.md、WCM.md、MANISKILL3.md、AHA_FAILGEN.md。这些历史明细保留，不因总报告替换而删除。',
 'ActiveVLA、AHA、ADV/VeGAS、VAP-TAMP、Thea、Self-Harness/Zetta 不列为已完成数值基线。旧状态审计仍保留其日期；本次特别复查 ActiveVLA 官方入口仍为待发布，因此不能将 AVA-VLA 的结果代替 ActiveVLA。[ACTIVECODE]',
]


def tex_escape(text):
    mapping = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#',
               '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
               '±': r'\(\pm\)', '×': r'\(\times\)'}
    result = ''.join(mapping.get(c, c) for c in text)
    for key, number in SOURCE_INDEX.items():
        result = result.replace(f'[{key}]', rf'\hyperlink{{src:{key}}}{{[{number}]}}')
    return result.replace('\n', r'\par ')


def md_text(text):
    for key, number in SOURCE_INDEX.items():
        text = text.replace(f'[{key}]', f'[{number}]({SOURCES[number-1][2]})')
    return text.replace('\n', '<br>')


def tex_table(headers, rows, widths, size='small'):
    cols = '@{}' + ''.join(f'L{{{w}mm}}' for w in widths) + '@{}'
    header = ' & '.join(r'\textbf{' + tex_escape(h) + '}' for h in headers) + r' \\ \midrule'
    body = '\n'.join(' & '.join(tex_escape(x) for x in row) + r' \\ \addlinespace[5pt]' for row in rows)
    return '\n'.join([r'\begingroup', rf'\{size}', r'\setlength{\tabcolsep}{3pt}',
                       rf'\begin{{longtable}}{{{cols}}}', r'\toprule', header, r'\endfirsthead',
                       r'\toprule', header, r'\endhead', r'\bottomrule\endfoot', body,
                       r'\end{longtable}', r'\endgroup'])


def md_table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '| ' + ' | '.join(['---'] * len(headers)) + ' |'] +
                     ['| ' + ' | '.join(md_text(x) for x in row) + ' |' for row in rows])


def build():
    rows = baseline_rows()
    counts = [int(row[3]) for row in SAMPLE]
    assert counts.count(2) == 5 and counts.count(3) == 3
    latex = [r'''% Generated by scripts/build_baseline_report.py; compile with XeLaTeX twice.
\documentclass[UTF8,11pt,a4paper,fontset=none]{ctexart}
\usepackage[margin=18mm,top=20mm,bottom=20mm]{geometry}
\usepackage{fontspec,booktabs,longtable,array,enumitem,fancyhdr,amsmath}
\usepackage[hidelinks,unicode]{hyperref}
\IfFontExistsTF{Microsoft YaHei}{\setCJKmainfont{Microsoft YaHei}\setCJKsansfont{Microsoft YaHei}}{\setCJKmainfont{Noto Sans CJK SC}\setCJKsansfont{Noto Sans CJK SC}}
\IfFontExistsTF{Arial}{\setmainfont{Arial}}{\setmainfont{TeX Gyre Heros}}
\setmonofont{Latin Modern Mono}
\setlength{\parindent}{0pt}\setlength{\parskip}{0.65em}
\renewcommand{\arraystretch}{1.18}
\newcolumntype{L}[1]{>{\raggedright\arraybackslash}p{#1}}
\ctexset{section={format=\Large\bfseries,beforeskip=0pt,afterskip=0.7em},subsection={format=\normalsize\bfseries,beforeskip=0.7em,afterskip=0.25em}}
\pagestyle{fancy}\fancyhf{}\fancyfoot[C]{\thepage}\renewcommand{\headrulewidth}{0pt}
\setlength{\emergencystretch}{2em}
\hypersetup{pdftitle={Baseline Report},pdfauthor={},pdfsubject={复现总表、2026评测核查与非饱和数据集}}
\begin{document}
\begin{titlepage}\thispagestyle{empty}\vspace*{0.34\textheight}
\begin{center}{\fontsize{30}{42}\selectfont\bfseries Baseline Report}\end{center}
\end{titlepage}
\setcounter{page}{1}
''']
    md = ['# Baseline Report', '']
    def section(title, paragraphs=None, subsections=None):
        latex.append(r'\clearpage\section{' + tex_escape(title) + '}')
        md.extend(['', '## ' + title, ''])
        for text in paragraphs or []:
            latex.append(tex_escape(text) + '\n')
            md.extend([md_text(text), ''])
        for heading, text in subsections or []:
            latex.extend([r'\subsection{' + tex_escape(heading) + '}', tex_escape(text) + '\n'])
            md.extend(['### ' + heading, '', md_text(text), ''])
    section('结论与阅读规则', INTRO + RULES)
    section('Baseline 五列总表')
    # A single continuing table, not several performance leaderboards.
    latex.extend([r'\begingroup\fontsize{9.2}{12.2}\selectfont\setlength{\tabcolsep}{2.5pt}',
                  r'\begin{longtable}{@{}L{22mm}L{25mm}L{39mm}L{38mm}L{41mm}@{}}',
                  r'\caption{既有实验总表：论文报告与本项目实际运行分别列示。}\\\toprule'])
    head = ' & '.join(r'{\bfseries ' + tex_escape(h).replace('performance(', r'performance\par (') + '}' for h in HEADERS) + r' \\\midrule'
    latex.extend([head, r'\endfirsthead', r'\multicolumn{5}{l}{\textbf{表 1（续）}}\\\toprule', head, r'\endhead',
                  r'\midrule\multicolumn{5}{r}{续下页}\\\endfoot', r'\bottomrule\endlastfoot'])
    mdrows = []
    previous = None
    for r in rows:
        if r['group'] != previous:
            latex.append(r'\multicolumn{5}{@{}l}{\textbf{' + tex_escape(r['group']) + r'}}\\*[3pt]')
            previous = r['group']
        fields = [r[k] for k in ['dataset', 'model', 'harness', 'reported', 'ours']]
        latex.append(' & '.join(tex_escape(x) for x in fields) + r' \\[6pt]')
        mdrows.append(fields)
    latex.extend([r'\end{longtable}\endgroup'])
    md.extend([md_table(HEADERS, mdrows), ''])
    section('结果解释与可改进空间', subsections=FINDINGS)
    section('2026 顶会的数据集数量核查', COUNTING[:2])
    sample_headers = ['论文', '会议', '仿真 benchmark', '计数', '真机与计数说明']
    latex.append(tex_table(sample_headers, SAMPLE, [30, 22, 51, 10, 49]))
    md.append(md_table(sample_headers, SAMPLE))
    for p in COUNTING[2:]:
        latex.append(tex_escape(p) + '\n'); md.extend(['', md_text(p), ''])
    section('数据集的剩余空间与取舍', [
        '“未饱和”在这里指：在明确版本、任务和训练条件下，强基线仍留下可研究的失败空间；不是对某数据集所有任务、所有模型的永久判断。以下论文数字不是最新全社区排行榜，更不是对不同 benchmark 的横向难度排序。',
    ])
    dataset_headers = ['数据集 / 协议', '可核验的性能证据', '本研究定位', '现有状态与边界']
    latex.append(tex_table(dataset_headers, DATASETS, [28, 54, 40, 44]))
    md.append(md_table(dataset_headers, DATASETS))
    section('确定的评测组合与资源边界', SELECTION)
    section('统一对照与论文使用条件', subsections=PROTOCOL)
    section('证据索引与参考来源', TRACE)
    latex.append(r'\begingroup\setlength{\parskip}{2pt}')
    for key, title, url in SOURCES:
        n = SOURCE_INDEX[key]
        latex.append(r'\par\hypertarget{src:' + key + '}{}' + f'[{n}] ' + r'\href{' + url + '}{' + tex_escape(title) + '}')
        md.append(f'{n}. [{title}]({url})')
    latex.extend([r'\endgroup', r'\end{document}'])
    PDF.mkdir(parents=True, exist_ok=True)
    (PDF / 'baseline_reproduction_report.tex').write_text('\n'.join(latex), encoding='utf-8', newline='\n')
    (DOC / 'BASELINE_REPORT.md').write_text('\n'.join(md), encoding='utf-8', newline='\n')
    (DOC / 'baseline_table.json').write_text(json.dumps(dict(
        columns=HEADERS, rows=rows, evidence_sha256=EVIDENCE,
        experiment_cutoff='2026-09-05', literature_checked='2026-09-13',
        sources=[dict(key=k, title=t, url=u) for k,t,u in SOURCES],
        conference_sample=SAMPLE, count_summary=dict(n=8, two=5, three=3, mean=statistics.mean(counts), median=statistics.median(counts)),
        notice='No new scientific experiments; not a matched-protocol leaderboard'), ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
    print(json.dumps(dict(rows=len(rows), evidence_files=len(EVIDENCE), paper_sample=len(SAMPLE), status='built'), indent=2))


if __name__ == '__main__':
    build()
