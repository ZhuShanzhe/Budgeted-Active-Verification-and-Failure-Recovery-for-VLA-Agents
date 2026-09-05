# 数据集与权重清单

**当前状态以 [2026-09-05 数据准备记录](DATASETS_20260905.md) 为准。** 本页以下是此前清单及排障背景：WidowX 与 Pi0-FAST/DROID 均已完整获得并用于训练测试，不能再按缺失资源处理；DROID 结果见 [补充复现](SAFE_DROID_20260905.md)。

## 已下载

| 资源 | 服务器路径 | 规模/状态 | 用途 |
|---|---|---:|---|
| LIBERO-Plus assets | `/root/autodl-tmp/datasets/LIBERO-plus-assets` | 压缩包约 6.4 GB，解压约 16 GB | 环境与七维扰动 |
| LIBERO-Plus LeRobot（四套压缩包） | `/root/autodl-tmp/datasets/libero-plus-4suite-lerobot-zips` | 17,291,020,751 字节；四包均通过 `unzip -tq` | WCM 数据管线与 OOD 评测；官方版本仅含成功轨迹 |
| WCM quick dataset | `/root/autodl-tmp/datasets/wcm-pick-place` | 约 55 MB | WCM 端到端快速复现 |
| WCM checkpoint | `/root/autodl-tmp/checkpoints/wcm-pick-place` | `best.pt` 约 683 MB | WCM 官方基线 |
| WCM backbones | `/root/autodl-tmp/checkpoints/wcm-backbones` 与 HF cache | ViT + CLIP | WCM 离线评测依赖 |
| AHA REFLECT subset | `third_party/AHA` 内 | 57 条记录 | 失败原因与标签结构 |
| OpenVLA-OFT checkpoint | `/root/autodl-tmp/checkpoints/openvla-7b-oft-libero-spatial` | 约 15 GB | 主策略基线 |
| AVA-VLA checkpoint | `/root/autodl-tmp/checkpoints/avavla-libero-4in1` | 约 15 GB | 主动视觉策略参考 |

## 未重复下载的大型副本

| 资源 | 规模 | 决策 |
|---|---:|---|
| LIBERO-Plus RLDS mixdata | 约 75.5 GB | 与已选 LeRobot 版内容重叠；当前 PyTorch 路线不需要 |
| LIBERO-Plus 四套打包数据 | 约 99.9 GB | 同时包含约 82.6 GB RLDS 与约 17.3 GB LeRobot 压缩包，避免重复 |
| RoboPoint co-training data | 约 291.1 GB | AHA 联合训练资源，不是主验证路线必要输入 |

## 需要人工授权或外部条件

| 资源 | 获取入口 | 阻塞原因 |
|---|---|---|
| SAFE Pi0-FAST rollouts | `https://drive.google.com/file/d/13z_cdwnaJota2iHkZbhYgVALujZwtM3b/view` | `gdown` 自动获取失败：共享权限或访问频率限制；需浏览器手工下载 |
| SAFE OpenVLA/WidowX rollouts | `https://drive.google.com/file/d/1EwaccasZjnlM9L6SEYyWqTd7d6-BR9zp/view` | `gdown` 自动获取失败：共享权限或访问频率限制；需浏览器手工下载。下载后上传到 `/root/autodl-tmp/datasets/safe-rollouts` |
| FailGen 全量失败轨迹 | AHA/ManiSkill-FailGen 生成脚本 | 不是固定下载包；需安装指定模拟器并按任务生成 |
| VAP-TAMP 实体数据 | 作者系统/设备 | 依赖 ROS2、OmniGibson、在线 API 和机器人硬件，单服务器不能补齐 |

## 数据版本规则

每个进入实验的数据集必须记录仓库 revision、下载日期、文件数、字节数和 SHA-256 manifest。训练集、校准集、ID 测试集与 OOD 测试集按场景/任务划分，禁止同一轨迹切片跨集合泄漏。

已生成三份 SHA-256 清单：`manifests/wcm-pick-place.json` 覆盖 11 个数据文件/55,180,249 字节，`manifests/wcm-pick-place-ckpt.json` 覆盖 4 个检查点文件/682,646,743 字节，`manifests/libero-plus-4suite-lerobot-zips.json` 覆盖 4 个压缩包/17,291,020,751 字节（revision `1a0f5c97a96e4187fbe52331b9a484f21d244bb2`）。

## 存储边界

2026-09-04 数据盘 `/root/autodl-tmp` 总计 1 TB，已用 111 GB，可用 890 GB；系统根盘总计 30 GB，已用 15 GB，可用 16 GB。当前不扩容。所有环境、缓存、数据、检查点与训练输出继续放在数据盘；系统根盘只保留操作系统和轻量工具。数据盘可用空间低于 250 GB，或开始同时保留多组全量优化器状态时，再执行归档或扩容。

生成清单：

```bash
python scripts/build_data_manifest.py DATASET_DIR \
  --revision HF_REVISION \
  --output manifests/DATASET_NAME.json
```
