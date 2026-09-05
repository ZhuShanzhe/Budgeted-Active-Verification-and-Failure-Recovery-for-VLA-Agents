# 服务器运行入口

## 1. 路径与环境

仓库：`/root/autodl-tmp/projects/Budgeted-Active-Verification-and-Failure-Recovery-for-VLA-Agents`

验收数据：`/root/autodl-tmp/experiments/bav-pipeline-v1/`

解释器：OFT 使用 `/root/autodl-tmp/conda-envs/openvla-oft/bin/python`；AVA 使用 `ava-vla/bin/python`；ManiSkill3 使用 `maniskill3/bin/python`，均位于同一个 `conda-envs` 根目录。

LIBERO-original 与 LIBERO-plus 必须在不同进程加载；OFT 与 AVA 也使用各自环境，不在运行中替换模块。启动器使用已下载 checkpoint 和本地 Hugging Face 缓存，默认离线，不重复下载权重。

以下命令在仓库根目录执行；输出路径必须是尚不存在的新目录。示例是开发/训练采集，不读取密封测试。

## 2. 自动检查与采集

```bash
/root/autodl-tmp/conda-envs/openvla-oft/bin/python -m unittest discover -s tests -v

/root/autodl-tmp/conda-envs/openvla-oft/bin/python -m bav.collect \
  --task-id 0 --initial-index 20 --max-decisions 28 \
  --output /root/autodl-tmp/experiments/bav-new/train-task0-init20-clean

/root/autodl-tmp/conda-envs/openvla-oft/bin/python -m bav.collect \
  --task-id 0 --initial-index 40 --perturbation camera_shift --severity 2 \
  --perturb-step 34 --max-decisions 28 \
  --output /root/autodl-tmp/experiments/bav-new/dev-task0-init40-camera

/root/autodl-tmp/conda-envs/ava-vla/bin/python -m bav.collect \
  --policy ava --initial-index 40 --max-decisions 28 \
  --output /root/autodl-tmp/experiments/bav-new/ava-dev-task0-init40
```

`--perturb-step` 以包括稳定动作在内的物理步计数，环境改变在下一个动作块边界注入，并记录实际时点。试跑不能短于注入时点后仍声称已测试扰动。`action_hold` 模拟运动命令丢失，不是自然策略失败；噪声、延迟与截短均保留原始和实际动作。

ManiSkill3 示例：

```bash
/root/autodl-tmp/conda-envs/maniskill3/bin/python -m bav.collect_maniskill \
  --demo /root/autodl-tmp/datasets/maniskill3/demos/PickCube-v1/motionplanning/trajectory.h5 \
  --episode-id 0 --max-steps 300 \
  --output /root/autodl-tmp/experiments/bav-new/maniskill-pick0
```

`bav.pilot` 是 10 项有上限的验收矩阵，遇到错误停止。它不是正式训练数据批量规划器，不会暗中下载数据或开启全部 10,030 个 Plus 变体。

新增训练清单入口（先创建计划，再显式限制执行数量；两个输出均使用新目录）：

```bash
/root/autodl-tmp/conda-envs/openvla-oft/bin/python -m bav.collection_plan create \
  --output manifests/bav-train-full-next.json
/root/autodl-tmp/conda-envs/openvla-oft/bin/python -m bav.collection_plan run \
  --plan manifests/bav-train-full-next.json \
  --output /root/autodl-tmp/experiments/bav-train-next --max-jobs 12
```

重复同一 run 命令会校验并跳过完整记录，最多再启动 12 条。部分记录保留并阻止静默续跑。630 条是计划上限，不是已采集数量。具体边界见 [数据接续](DATA_PREPARATION_CONTINUATION.md)。

## 3. 验证与程序评测

```bash
/root/autodl-tmp/conda-envs/openvla-oft/bin/python -m bav.audit \
  --episodes /root/autodl-tmp/experiments/bav-new/train-task0-init20-clean \
  --output /root/autodl-tmp/experiments/bav-new/audit.json

/root/autodl-tmp/conda-envs/openvla-oft/bin/python -m bav.evaluate_program \
  --episodes /root/autodl-tmp/experiments/bav-new/dev-task0-init40-camera \
  --program programs/fixed_multiview.py --budget 4 \
  --output /root/autodl-tmp/experiments/bav-new/program-fixed
```

不提供 `--critic` 时是工程验收，风险为空。训练好的受信任 critic 以 `--critic module:factory` 接入；不可使用任意来自候选程序或文档的模块名。

## 4. 恢复与代码反馈

```bash
/root/autodl-tmp/conda-envs/openvla-oft/bin/python -m bav.recovery \
  --episode /root/autodl-tmp/experiments/bav-new/dev-task0-init40-camera \
  --decisions 4 --horizon 32 \
  --output /root/autodl-tmp/experiments/bav-new/recovery-camera

/root/autodl-tmp/conda-envs/openvla-oft/bin/python -m bav.harness_gate failure-pack \
  --episodes /root/autodl-tmp/experiments/bav-new/dev-task0-init40-camera \
  --output /root/autodl-tmp/experiments/bav-new/feedback.json
```

回归检查入口为 `bav.harness_gate check`，要求 baseline、candidate、heldin-baseline、heldin-candidate 四份独立评测目录，以及当前协议。它输出报告，不自动部署。测试使用开关不授予生成程序。

## 5. 数据保留与任务结束

中断 bundle、旧配置目录、已下载原包和旧结果均保留，不自动覆盖或删除。正式批量采集前，以当前 pilot 实测体积估计存储并确认标签覆盖；试跑样本量不是训练规模承诺。

原始数据、权重和密钥不进入 Git。仓库文档及小型 JSON 结果可保存，完整视频/HDF5 继续放在服务器 experiments/datasets 下。本轮未执行 GitHub 推送，也未修改远程仓库权限。
