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
\hypersetup{pdftitle={Baseline Report},pdfauthor={},pdfsubject={复现总表与有提升空间的数据集}}
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
        notice='No new scientific experiments; not a matched-protocol leaderboard'), ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
    print(json.dumps(dict(rows=len(rows), evidence_files=len(EVIDENCE), status='built'), indent=2))


if __name__ == '__main__':
    build()
