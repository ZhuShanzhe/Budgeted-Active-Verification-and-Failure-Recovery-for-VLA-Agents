# 补充复现的上游可用性核查

审计日期：2026-09-05。核查区分“公开论文”“可执行源码”“可下载权重”和“当前服务器能够完成有意义的评测”，不以安装、导入、mock 测试代替性能复现。

## 本轮补充范围

SAFE 作者实现中的 cosine / Euclidean kNN 检测器已在 WidowX、DROID 两域、三个既定种子上完成 12 组评测。RND 使用相同划分，六组 200 epoch 训练、加载后测试及 DROID 独立指标/标签敏感性检查已全部完成。它们与后续 critic 有直接比较关系，且无需训练大型执行策略。

I-FailSense 是本轮新增的外部视觉失败检测参考。PaliGemma2 许可、服务器认证、模型传输和校验均已完成。单视角 CALVIN 作者 validation 派生的 203 样本已全部评测：完整模型 184/203，VLM 组件 174/203，逐例配对及独立指标重算通过。详见 [I-FailSense 记录](IFAILSENSE_20260905.md)，不等同于整篇论文或未触碰 OOD 主测试。

## 逐项资源核查

| 工作 | 上游证据 | 本轮判断 |
|---|---|---|
| ActiveVLA | [官方仓库](https://github.com/ZhenyangLiu/ActiveVLA-Injecting-Active-Perception-into-VLA)，审计提交 4450b1188a24f3f1d1d3fb3e47d226d150b9e470；代码、权重、评测仍待发布 | 不能开展原模型定量复现；保留为主动观察设计参考 |
| AHA | [NVlabs/AHA](https://github.com/NVlabs/AHA)；当前上游提交 0d39c0591566ddaf997be5822f3dead8e08501aa；从头训练流程约需 8 张 A100 80GB、40 小时及约 291GB 联合训练数据 | 尚未找到最终可直接评测的 critic 权重；单张 32GB GPU 不具备原方案完整训练条件；FailGen 的现有结果单独保留 |
| ADV | [论文](https://arxiv.org/abs/2603.18091) | 本次检索仍未定位可执行的官方代码和评测入口；不以自写简化版本冒充复现 |
| VeGAS | [作者仓库](https://github.com/nishadsinghi/vegas)，README 标注 Code Coming Soon | 仓库已找到，修正旧记录；目前仍不能运行。仓库标注 CVPR 2026 Findings，不写成主会接收 |
| VAP-TAMP | [官方仓库](https://github.com/aoloo-r/VAP-TAMP) | 完整系统涉及 ROS2、OmniGibson、Gemini 与机器人平台；当前条件不足以复现原系统结果 |
| Thea | [官方仓库](https://github.com/EIT-HAI/Thea) | 公开预览运行时需自备模型后端、episode、policy 和 evaluator；直接 Python 入口并非必须使用 Lark；接口检查不是论文级性能复现 |
| Zetta | [官方仓库](https://github.com/air-embodied-brain/Zetta-Embodiment) | 提供真实 campaign 框架，但完整实验依赖指定策略/环境和 coding 模型后端；例如 LIBERO-Pro/Pi0.5、RoboCasa/GR00T。既有 OFT 不能直接当作原协议策略 |
| I-FailSense | [作者仓库](https://github.com/clemgris/I-FailSense)，提交 0c71f564cece59816733a8d9ac58ee62b264bf8c；[论文](https://arxiv.org/abs/2509.16072)；作者标注 ICRA 2026 | FS release 782,100,486 字节及底座、LoRA 均已校验；完整模型与 VLM 组件各完成 203 条测试，无跳过 |

## I-FailSense 评测边界

- 优先固定作者单视角 CALVIN 模型与配套 FS 权重，再按作者的数据定义评测，不在测试集上挑 checkpoint。
- 作者 DROID benchmark（例如 ACIDE/DROID_1p_bench）与 SAFE 的 Pi0-FAST/DROID rollout 并非同一数据集；前者的构造及指令扰动必须单独记录。
- 作者训练脚本存在使用外部测试资源作验证/模型选择的路径。发布检查点的实际训练暴露范围未充分证明时，不声称“完全未见的 OOD 测试”。
- 投票结果是分类器与 VLM 的票数比例，不自动是已校准的失败概率。
- 本地工程修正、精度、batch、权重选择、评测样本数量与失败样本处理均须显式记录；不能静默跳过异常推理。

## 未开展的工作不折算为零分

未复现项只进入相关工作和资源状态表，不进入数值排名。上述“未找到”是本轮可见资源范围内的结论，不表示资源永久不存在。新的公开资源或合法访问条件就绪后，可在冻结协议下追加独立结果，保留既有实验版本。
