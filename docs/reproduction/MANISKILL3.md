# ManiSkill3 与小型失败生成环境

## 安装范围

独立 Python 3.12 虚拟环境：`/root/autodl-tmp/conda-envs/maniskill3`。虽然放在统一环境目录下，它是 venv，不是 conda 环境；直接使用其 `bin/python` 或 `source .../bin/activate`。

固定兼容组合为 ManiSkill 3.0.1、SAPIEN 3.0.3、MPlib 0.1.1、Gymnasium 0.29.1、NumPy 1.26.4、SciPy 1.14.1、OpenCV 4.11.0.86。PyTorch 继承服务器基础环境；实际版本记录见 `results/20260905/environment_versions.json`。没有修改 OFT、AVA、SAFE、WCM 的独立环境。

## 已验证能力

| 任务 | RGB-D 相机 | 环境结果字段 | 外部演示重放 |
|---|---|---|---|
| PickCube-v1 | base_camera | 抓取、放置、静止、成功 | 前 3 条，3/3 成功 |
| StackCube-v1 | base_camera、hand_camera | 抓取、堆叠位置、静止、成功 | 前 3 条，3/3 成功 |
| PegInsertionSide-v1 | base_camera、hand_camera | 插入位置、成功 | 前 3 条，3/3 成功 |

环境 smoke 检查采用 128×128 图像，RGB 与 depth 数据形状和有限性检查通过。运行 CPU 物理仿真与 GPU 渲染。SAPIEN 对系统 Vulkan 配置发出警告后使用自带回退实现；实际渲染已经通过，不把该警告误记为环境不可用。

演示重放执行原始动作，不通过逐帧设置真值状态伪造执行成功；保留失败开关开启、重试次数为 0。这里检查的是数据可用性，不是训练策略泛化能力。

本批派生重放没有保存每帧完整物理环境状态；RGB-D 与机器人观测可用于读取测试，但尚不是支持任意状态分叉、证据成本与恢复对照的正式采集数据。

## 输入输出位置

- 外部演示：`/root/autodl-tmp/datasets/maniskill3/demos`。
- 外部资产与后续资产下载位置：`/root/autodl-tmp/datasets/maniskill3/assets`；几何任务基础资产随软件包提供。
- RGB-D 重放产物：`/root/autodl-tmp/experiments/baselines-20260905/maniskill-replay`。
- 环境检查与 FailGen 输出：同一实验根目录下 `maniskill3-smoke`、`failgen-smoke`。
- 紧凑审计结果：`results/20260905/maniskill_replay_summary.json`、`maniskill3-smoke/summary.json`、`failgen-smoke/summary.json`。

## 执行入口

```bash
/root/autodl-tmp/conda-envs/maniskill3/bin/python scripts/smoke_maniskill3.py
bash scripts/replay_maniskill_demos.sh
/root/autodl-tmp/conda-envs/maniskill3/bin/python scripts/smoke_failgen.py
```

FailGen 的 8 次检查不是完整训练集，具体标签和输出限制见 [AHA/FailGen](AHA_FAILGEN.md)。本轮没有把 LIBERO 策略直接套到不同机器人/控制器的 ManiSkill 环境后声称零样本性能。

来源：[ManiSkill](https://github.com/mani-skill/ManiSkill)、[演示说明](https://maniskill.readthedocs.io/en/latest/user_guide/datasets/demos.html)、[ManiSkill-FailGen](https://github.com/wpumacay/maniskill-failgen)。
