# OpenVLA-OFT 与 AVA-VLA

## OpenVLA-OFT

- **状态：L2 链路复现。**
- 官方 `openvla-7b-oft-finetuned-libero-spatial` 7.54B 权重已加载。
- 真实 LIBERO 观测经过预处理、模型前向和动作反归一化，得到 `(8, 7)` 动作块；数值全部有限。
- 单次前向耗时约 0.755 秒；日志：`/root/autodl-tmp/logs/openvla_oft_smoke.log`。

结论：模型链路可作为主策略接口，但尚未执行 LIBERO 全任务、多随机种子 rollout，因此不得把单步结果表述为任务成功率复现。

## AVA-VLA

- **状态：L2 链路复现。**
- 官方 `avavla-libero-4in1` 7.54B 权重已加载。
- 真实 LIBERO 观测完成前向并输出 `(8, 7)` 有限动作块。
- 单次前向耗时约 0.794 秒；日志：`/root/autodl-tmp/logs/avavla_smoke.log`。

结论：AVA-VLA 可作为包含主动视觉输入机制的强策略参考，但目前同样没有完整任务成功率。后续统一使用同一 LIBERO/LIBERO-Plus episode、相同种子和相同预算协议，与本方法比较成功率、查询成本和失败恢复率。
