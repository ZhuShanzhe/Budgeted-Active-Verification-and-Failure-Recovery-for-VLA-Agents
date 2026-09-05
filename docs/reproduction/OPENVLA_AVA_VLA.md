# OpenVLA-OFT 与 AVA-VLA

## 2026-09-05：实际闭环评测

同一组原版 LIBERO Spatial 初始状态，10 个任务、每任务前 5 个官方初始状态，共 50 次，随机种子 7。OFT 为 50/50（100%），AVA-VLA 为 48/50（96%）。这是冻结小样本协议的实际成功率，不是每任务 50 次的官方全量成绩。Wilson 95% 区间分别为 [92.87%, 100%]、[86.54%, 98.90%]；轨迹按任务聚集，区间仅作描述性参考，不据此宣称显著优劣。

执行上游 episode loop、双相机输入、proprio、256 像素环境渲染、8 步 action chunk、10 步稳定等待与 Spatial 的 220 步上限。全局/策略种子为 7；上游 `get_libero_env` 按其原实现固定环境种子为 0，两种策略一致。AVA 使用发布配置的历史动作特征与注意力机制。预训练范围不同：OFT 为空间套件专用权重，AVA 为四套件联合权重，不能把差异完全归因于注意力模块。

逐轨迹结果、配置、任务名单和源码提交保存在 `results/20260905/{oft,ava}-clean-spatial-50/`；服务器完整输出在 `/root/autodl-tmp/experiments/baselines-20260905/`。执行入口为 `scripts/run_policy_matrix.sh`。

原有环境的 `libero` 指向 LIBERO-Plus，不能用于标准分数。新增 `third_party/LIBERO-original` 和每次运行独立的 LIBERO 配置，检查实际导入位置与任务数等于 10。早期错误入口试跑目录 `oft-spatial-50` 未纳入任何正式汇总。

记录了实际查询次数、推理时长与显存，但本批部分时间与 SAFE/环境检查共享 GPU；这些是运行记录，不是严格隔离负载的算法延迟对比。最终论文的效率表需要独立计时、预热和重复测量。

两种策略还各完成 LIBERO-Plus 七维固定 70 任务诊断：OFT 58/70，AVA 55/70。由于上游提示词包含部分扰动后缀，该结果不进入严格的单因素 OOD 主表；分类结果和协议边界见 [LIBERO-Plus](LIBERO_PLUS.md)。标准与扰动共 240 次执行的配对审计通过。

## 历史单步检查

### OpenVLA-OFT（历史检查，不代表当前最高完成度）

- **状态：L2 链路复现。**
- 官方 `openvla-7b-oft-finetuned-libero-spatial` 7.54B 权重已加载。
- 真实 LIBERO 观测经过预处理、模型前向和动作反归一化，得到 `(8, 7)` 动作块；数值全部有限。
- 单次前向耗时约 0.755 秒；日志：`/root/autodl-tmp/logs/openvla_oft_smoke.log`。

结论：模型链路可作为主策略接口，但尚未执行 LIBERO 全任务、多随机种子 rollout，因此不得把单步结果表述为任务成功率复现。

### AVA-VLA（历史检查，不代表当前最高完成度）

- **状态：L2 链路复现。**
- 官方 `avavla-libero-4in1` 7.54B 权重已加载。
- 真实 LIBERO 观测完成前向并输出 `(8, 7)` 有限动作块。
- 单次前向耗时约 0.794 秒；日志：`/root/autodl-tmp/logs/avavla_smoke.log`。

当时结论：AVA-VLA 的视觉注意力与历史特征策略链路可执行，单步检查没有提供任务成功率。当前有限协议的闭环结果见本页开头。AVA-VLA 不等同于 ActiveVLA，也不等同于本项目的成本感知证据查询路由器。
