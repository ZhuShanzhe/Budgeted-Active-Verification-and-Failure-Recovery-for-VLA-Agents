# WCM

- **状态：L3（公开 pick-place quick benchmark）；论文全套任务未复现。**
- 上游提交：`d028ebb`（审计副本）。
- 官方快速数据 `Sylvest/pick-place-wcm` 已下载，约 55 MB。
- 官方检查点 `Sylvest/pick-place-wcm-ckpt` 已下载，核心权重 `best.pt` 约 683 MB。
- 独立环境：Python 3.12、PyTorch 2.7.1+cu128、torchvision 0.22.1+cu128；RTX 5090 BF16 运算通过。
- 官方验证 split 已完整评测：18 个 episode、1,617 个时序窗口、102 个 batch。

## 复现结果

| 指标 | 结果 |
|---|---:|
| value RMSE | 0.380342 |
| value MAE | 0.196550 |
| value Pearson | 0.720664 |
| token value RMSE | 0.383271 |
| token value Pearson | 0.716935 |
| next-state MSE | 0.007358 |
| token next-state MSE | 0.007333 |

可提交的原始结果位于 `docs/reproduction/results/WCM/`，包含 `summary.json`、逐 episode 指标与曲线 CSV。完整图像位于服务器 `/root/autodl-tmp/experiments/wcm/full-val/episode_curves/`；执行日志：`/root/autodl-tmp/logs/wcm_full_val.log`。

官方说明该 LIBERO-Plus 发布集只含成功轨迹。因此它适合检验数据管线和动力学表征，但不能单独训练有判别力的失败 critic；主实验仍需加入 FailGen 和本项目采集的失败/恢复轨迹。

## 可借鉴内容

WCM 用历史观测预测未来状态，适合作为部分可观测条件下的短时序表征。项目仅采用其世界模型/时序 critic 能力，不进行大规模 VLA-RL；对比重点为单帧 critic、固定历史窗口 WCM 和主动证据路由三者的风险—成本曲线。

## 使用边界

这些数值可作为官方公开 pick-place 资源的 WCM 基线。它们不是 WCM 论文中 ManiSkill、MetaWorld、CALVIN、LIBERO-Plus 与真实机器人七任务的全量复现，不能外推为整篇论文结果。后续主论文对照需在本项目冻结的 LIBERO-Plus 失败/恢复 split 上重新训练或评测同一 WCM 结构。

来源：https://github.com/sylvestf/WCM
