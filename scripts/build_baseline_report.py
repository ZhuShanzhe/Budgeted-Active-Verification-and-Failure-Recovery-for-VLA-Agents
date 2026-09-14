"""Build the baseline report from audited results; never run or modify experiments.

Usage: python scripts/build_baseline_report.py
Then compile docs/reproduction/pdf/baseline_reproduction_report.tex with XeLaTeX twice.
"""
from pathlib import Path
import hashlib
import json
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
 ('PLUSNUM', 'LIBERO-Plus：作者论文完整表与各套件明细', 'https://arxiv.org/pdf/2510.13626'),
 ('SAFE', 'SAFE：NeurIPS 2025，Table 8、B.8 与真实 Franka 实验', 'https://arxiv.org/html/2506.09937v2'),
 ('IFS', 'I-FailSense：Table I 与评测定义', 'https://arxiv.org/html/2509.16072v1'),
 ('WCM', 'WCM：作者公开 quick benchmark、数据与权重', 'https://github.com/sylvestf/WCM'),
 ('MEM', 'MemoryVLA：ICLR 2026；4.1-4.5，Table 4', 'https://arxiv.org/html/2508.19236v2'),
 ('MIKASA', 'MIKASA-Robo：官方数据、环境与版本说明', 'https://github.com/CognitiveAISystems/MIKASA-Robo'),
 ('ROBOCASA', 'RoboCasa365：Table 2，目标任务微调后的成功率', 'https://arxiv.org/html/2603.04356'),
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


RULES = [
 'SR / accuracy 用百分数；AUROC / AUPRC 用 0-100 尺度。本次 SAFE 为三种子均值±样本标准差，采用每任务最短轨迹窗口内最大风险分数；不代表实际检测提前量。',
 'NR：论文未给出对应域/协议值；N/A：非模型性能。两列并排不等于同协议比较；样本量、调优范围和 Plus 旧提示词混杂已在表内标明。',
]

DATASET_NOTES = [
 ('LIBERO-Plus：扰动下的主动验证与恢复',
  '作者报告 OFT 全套件 SR 69.6%，其中相机扰动 56.4%、初态扰动 31.9%；mix-SFT 整体 79.5%，仍有提升空间。[PLUSNUM] 本研究用于视觉/初态等分布变化下的证据获取与失败恢复。代码和资产已有；现有 70 次结果含提示词混杂，仅作诊断，正式比较须使用冻结的无混杂协议。'),
 ('MIKASA-Robo：历史证据与部分可观测判断',
  'MemoryVLA 论文五任务协议中，OFT SR 28.4%、MemoryVLA 41.2%。[MEM] 该协议包括 ShellGameTouch、InterceptMedium、RememberColor3/5/9，适合检验历史检索和证据不足判断。环境与数据公开，但本项目尚未接入或复现；不能将旧五任务成绩套到当前 90 任务版本。[MIKASA] 模型只能查询真实保存的历史，不获取未记录的过去或状态真值。'),
 ('SAFE Pi0-FAST / DROID：真实跨任务失败检测',
  '论文 Real Franka 列中 MLP 的未见任务 AUROC 为 64.16，本次固定配置为 53.53；该差距含调优协议差异，不能直接视作新方法可获得的增益。[SAFE] 已有 1,464 条原始 rollout、780 条既用筛选数据，可用于真实域离线验证。它不是 DROID 全集，也不提供交互式新视角或真实恢复反事实；标签异常与既往数据使用须保留记录。'),
 ('RoboCasa365：长时序家庭操作扩展',
  '论文 Table 2 的 GR00T N1.5 在预训练＋目标全数据微调设置下，atomic SR 68.5%、composite-seen 40.6%、composite-unseen 42.1%。[ROBOCASA] 复合任务仍有明显空间，适合环境反馈与阶段性恢复。该数据集作为扩展项，尚未完成本项目基线；控制适配与长时序采集成本较高，不与旧版 RoboCasa 成绩混用。'),
]

HARNESS_INTRO = 'Model 指执行预测的模型；harness 指组织输入、模型调用、动作执行、结果判定与记录的外围流程。H1-H9 是本报告的流程编号，不是九种论文方法，也不是九套已完成的主动验证系统。训练轮数与种子属于实验配置，不属于决策机制。'
HARNESS_NOTES = [
 ('H1：标准策略执行循环', [
  ('适用与输入', 'OpenVLA-OFT / AVA-VLA，标准 LIBERO Spatial。输入为任务指令、双相机图像和机器人本体状态。'),
  ('执行流程', '读取观测 → 策略生成 8 步动作块 → 环境执行 → 获取新观测 → 重复，成功或达到步数上限时结束。本批包含 10 步稳定等待，任务执行上限为 220 步。'),
  ('输出与边界', '输出逐轨迹成功与否及执行记录。AVA 使用其发布配置的历史动作特征和注意力机制，属于模型内部能力；外层没有附加 critic、主动查询或独立恢复模块。策略自行纠偏不等于外加恢复系统。'),
  ('研究位置', '无附加验证的执行策略对照。两种发布权重训练范围不同，当前差异不能全部归因于注意力机制。'),
 ]),
 ('H2：扰动环境中的策略执行', [
  ('适用与输入', 'OpenVLA-OFT / AVA-VLA，LIBERO-Plus Spatial 子集。两策略使用同一评测名单，输入权限与 H1 同类。'),
  ('执行流程', '选定扰动任务与初态 → 运行标准策略循环 → 环境判定结果 → 按扰动维度汇总。相机、布局、光照、语言、纹理、初态和传感器噪声七轴各 10 次。'),
  ('输出与边界', '输出扰动下成功率；没有增加异常检测、主动观察或恢复决策。旧运行部分指令混入扰动名称，成绩仅作实现诊断。'),
  ('研究位置', 'H1 的扰动评测版本，不是另一种主动 harness。正式 OOD 对照使用消除非目标提示词混杂的冻结协议；语言扰动本身与意外后缀分开处理。'),
 ]),
 ('H3：学习型被动失败监测', [
  ('适用与输入', 'SAFE-MLP / SAFE-LSTM；分别使用 WidowX 与 DROID 已记录的 VLA 内部特征及轨迹标签，需要白盒特征访问。'),
  ('执行流程', '按任务划分数据 → 固定配置训练检测器 → 读取测试轨迹特征并输出逐时刻风险 → 汇总评分 → 使用独立校准数据确定报警阈值。MLP 映射特征，LSTM 利用时序信息。'),
  ('输出与边界', '三种子、每种子 1,000 epoch。仅离线评分与校准，不改变机器人动作；总表采用统一窗口内最大风险的 AUROC/AUPRC，不表示检测提前量或恢复收益。OOD 下校准目标不自动成为误报保证。'),
  ('研究位置', '已有证据上的被动风险检测对照；不判断缺少哪类证据，也不主动调用外部视觉工具。'),
 ]),
 ('H4：基于特征检索的被动监测', [
  ('适用与输入', 'SAFE 官方 Cosine / Euclidean kNN；数据、任务划分与 H3 相同，两域分别建立特征库。'),
  ('执行流程', '用训练轨迹有效时间步建立成功库和失败库 → 查询特征分别检索 k=5 近邻 → 以到成功库的距离减去到失败库的距离构造风险 → 评分与阈值校准。'),
  ('输出与边界', '两者仅距离度量不同，无梯度训练；特征库显式保存并重新加载验证。检索仍有存储与计算成本，不能把无需训练写成零成本。测试数据不参与建库。'),
  ('研究位置', '简单、可解释的风险对照。未见任务可能只是远离训练特征，并非执行失败；该机制不获取新的视觉证据。'),
 ]),
 ('H5：预测误差式被动监测', [
  ('适用与输入', 'SAFE 官方 RND；使用与 H3 相同的策略特征、轨迹筛选和任务划分。'),
  ('执行流程', '特征进入固定随机目标网络与可训练预测网络 → 按官方损失训练 → 根据预测误差构造风险 → 逐轨迹评分与校准。当前配置中成功和失败均参与训练，不是仅用成功数据的普通异常检测。'),
  ('输出与边界', '三种子、每种子 200 epoch；小尾批并入前批以避免原损失的数值异常，不丢弃轨迹。当前固定配置的检测排序较弱，不代表完整调参后的能力上限。'),
  ('研究位置', '另一类被动风险信号。陌生程度不等于失败程度；没有主动查询、动作干预或恢复执行。'),
 ]),
 ('H6：视觉语义失败判断', [
  ('适用与输入', 'I-FailSense；单视角时序拼图与任务文本。固定公开底座、LoRA 和分类器权重，在作者 validation 派生的同一批 203 样本上评测，不重新训练。'),
  ('执行流程', '完整模型：图文输入 → VLM 特征与解码判断 → 三路分类器与 VLM 加权投票 → 成功/失败。组件对照：相同图文输入 → LoRA/VLM 单 token 解码 → 按作者规则映射标签，不调用完整分类器组合。'),
  ('输出与边界', '输出逐样本判断与 accuracy；完整模型票数比例不是校准概率。该批数据不是自行冻结的全新 OOD 测试集，离线识别也不等于在线恢复。'),
  ('研究位置', '任务条件视觉验证工具的参考。输入证据预先固定，没有主动换视角、证据预算分配或恢复闭环。'),
 ]),
 ('H7：固定历史窗口预测', [
  ('适用与输入', 'WCM 官方 pick-place quick benchmark 与公开检查点；18 个 episode、1,617 个历史时序窗口。'),
  ('执行流程', '按官方验证划分构造窗口 → 固定 WCM 前向预测价值与下一状态 → 与数据目标比较 → 汇总预测误差和相关性。'),
  ('输出与边界', '报告价值 RMSE、MAE、Pearson 和下一状态 MSE。没有执行完整 VLA-RL 控制闭环；公开 quick benchmark 只含成功轨迹，不能单独证明失败检测或恢复能力。'),
  ('研究位置', '部分可观测条件下的历史表征参考。固定窗口不会决定何时检索历史、选择哪些证据或何时停止查询。'),
 ]),
 ('H8：官方演示动作回放', [
  ('适用与输入', 'ManiSkill3 的 PickCube、StackCube、PegInsertionSide，各 3 条官方演示；输入为演示初态和动作序列。'),
  ('执行流程', '加载演示与初态 → 在仿真中执行记录动作 → 读取环境终局判定 → 汇总回放结果。执行动作，不逐帧强制写入演示状态。'),
  ('输出与边界', '9/9 回放成功。没有学习模型根据图像作决策，因此不是策略成功率基线，只证明选定演示、动作接口和环境执行链路可用。'),
  ('研究位置', '第二环境的数据采集与执行接口验收，不与新模型的性能直接排名。'),
 ]),
 ('H9：程序化扰动与结果标注', [
  ('适用与输入', 'ManiSkill-FailGen；PickCube / StackCube，grasp / trans_x 两类扰动，种子 7/8，共 8 次运行。'),
  ('执行流程', '选定任务与扰动配置 → 注入抓取或平移扰动并继续执行 → 读取环境实际结果 → 保存生成图像及成功/失败记录。扰动注入本身不作为失败标签。'),
  ('输出与边界', '8/8 链路完成，其中 4 成功、4 失败。当前上游入口主要保存多视角拼接帧，未构成含完整时序、动作、证据成本和恢复分支的正式训练数据集；不是 AHA critic 的准确率。'),
  ('研究位置', '可控失败案例生成工具。用于后续数据管线扩展，不是失败检测模型或已经完成的恢复系统。'),
 ]),
]


def tex_escape(text):
    mapping = {'\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#',
               '_': r'\_', '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
               '±': r'\(\pm\)', '×': r'\(\times\)'}
    result = ''.join(mapping.get(c, c) for c in text)
    for key, number in SOURCE_INDEX.items():
        result = result.replace(f'[{key}]', rf'\href{{{SOURCES[number-1][2]}}}{{[{number}]}}')
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
\hypersetup{pdftitle={Baseline Report},pdfauthor={},pdfsubject={复现总表、Harness 流程与有提升空间的数据集}}
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
    latex.append(r'\begingroup\small')
    for note in RULES:
        latex.append(tex_escape(note) + '\n')
        md.extend([md_text(note), ''])
    latex.append(r'\endgroup')
    section('Harness 含义与执行流程', [HARNESS_INTRO])
    for index, (heading, fields) in enumerate(HARNESS_NOTES):
        if index in (3, 6):
            latex.append(r'\clearpage')
        latex.append(r'\subsection*{' + tex_escape(heading) + '}')
        md.extend(['### ' + heading, ''])
        for label, content in fields:
            latex.append(r'\textbf{' + tex_escape(label) + '：}' + tex_escape(content) + '\n')
            md.extend([f'**{label}：**' + md_text(content), ''])
    section('有提升空间的数据集', [
        '以下为特定版本与协议下的性能证据，不是全社区最新排名；剩余失败也不一定都可由主动观察解决。标准 LIBERO 仅保留为干净控制项，不作为主要提升空间。',
    ], subsections=DATASET_NOTES)
    latex.append(r'\end{document}')
    PDF.mkdir(parents=True, exist_ok=True)
    (PDF / 'baseline_reproduction_report.tex').write_text('\n'.join(latex), encoding='utf-8', newline='\n')
    (DOC / 'BASELINE_REPORT.md').write_text('\n'.join(md), encoding='utf-8', newline='\n')
    (DOC / 'baseline_table.json').write_text(json.dumps(dict(
        columns=HEADERS, rows=rows, evidence_sha256=EVIDENCE,
        experiment_cutoff='2026-09-05', literature_checked='2026-09-13',
        sources=[dict(key=k, title=t, url=u) for k,t,u in SOURCES],
        dataset_notes=DATASET_NOTES,
        harness_intro=HARNESS_INTRO, harness_notes=HARNESS_NOTES,
        notice='No new scientific experiments; not a matched-protocol leaderboard'), ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
    print(json.dumps(dict(rows=len(rows), evidence_files=len(EVIDENCE), status='built'), indent=2))


if __name__ == '__main__':
    build()
