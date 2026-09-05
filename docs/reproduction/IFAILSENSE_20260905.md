# I-FailSense：外部视觉失败检测参考

## 预先固定的评测协议

采用作者的单视角 CALVIN 配置，不在测试集上选择模型：

- 上游：[clemgris/I-FailSense](https://github.com/clemgris/I-FailSense)，提交 `0c71f564cece59816733a8d9ac58ee62b264bf8c`。作者标注 ICRA 2026；[论文](https://arxiv.org/abs/2509.16072)。
- 底座：`google/paligemma2-3b-mix-224`，revision `8e40ab4cc5df93dfb7fd2fff754bcdff8b62ee78`；已通过合法访问认证。
- LoRA：`ACIDE/FailSense-Calvin-1p-3b`，revision `83315e88033ec3e7a5682866d7cb9666f754e36c`。
- FS：作者 release 内 `FS/FailSense-Calvin-1p-3b/components_epoch_10.pt`；选择在完整模型推理前固定。
- 数据：`ACIDE/AHA-Calvin-1p`，revision `766072fb821ae6b57d0a4a213a4021cb5f5b98ed`。仅下载 80,891,538 字节的 validation parquet，不下载本轮不需要的训练集。
- 数据划分：2,022 条 validation，按作者 `train_test_split(test_size=0.1, seed=42)['test']` 得到 203 条；97 失败、106 成功。保存源行号和逐样本结果。
- batch 4、FP32，不量化；单视角图像和任务文本；保持作者 prompt、特征层、池化、分类器和投票逻辑。不重新训练底座、LoRA 或 FS。

环境：隔离的 `ifailsense` 环境，PyTorch 2.11.0+cu128、Transformers 4.55.4、PEFT 0.17.1、Datasets 3.6.0；继承已安装 PyTorch，不改动 OFT 原有依赖。模型文件校验后离线评测。

## 已完成：VLM 组件对照

调用作者 `extract_features(..., voting=True)` 的单个下一 token 解码，按原投票逻辑把 success/1/pass 映射成功，把 fail/0/failure 映射失败。其余输出保留为拒答，并在全样本准确率中计错；本批没有拒答。

| 指标 | 实测值 |
|---|---:|
| 全部测试样本 | 203 |
| 正确数 / 准确率 | 174 / 203，85.7143% |
| 平衡准确率 | 85.7080% |
| 失败样本正确数 | 83 / 97 |
| 成功样本正确数 | 91 / 106 |
| 拒答 / 静默跳过 | 0 / 0 |

这是已发布 VLM 组件的诊断对照，**不是完整 I-FailSense**。原构造器会分配随机 FS 模块，但本次完全不调用它们的预测；没有拿随机分类器输出充当模型结果。记录的推理总耗时约 9.69 秒只作本机运行审计，不是跨方法效率主表。

## 完整模型与数据使用边界

完整模型已完成全部 203 条推理，无跳过。分类器 ZIP 782,100,486 字节，SHA-256 `3b5240c999b675c9f78f01b8dac3f05003bbbd072ad8356fe3d78dbdbd2986f4` 与发布方一致；上传后的远端哈希及 ZIP 全条目 CRC 检查通过。只提取预先选定的 1p epoch 10 权重。

| 指标 | 完整 I-FailSense | VLM 组件 |
|---|---:|---:|
| 正确数 / 准确率 | 184 / 203，90.6404% | 174 / 203，85.7143% |
| 平衡准确率 | 90.4688% | 85.7080% |
| 失败识别正确数 | 84 / 97 | 83 / 97 |
| 成功识别正确数 | 100 / 106 | 91 / 106 |
| failure F1 | 0.898396 | 未作为预设组件指标 |
| failure AUROC | 0.943153 | 硬解码，不报告连续分数 AUROC |
| failure AUPRC（曲线积分） | 0.958347 | 同上 |

两个运行的 203 个源行号及标签完全一致。配对结果：共同正确 171 条，仅完整模型正确 13 条，仅组件正确 3 条，共同错误 16 条；准确率差 4.9261 个百分点。完整模型改善主要来自成功样本误报减少，失败检出仅净增 1 条。不把该小型组件对照外推成主动观察或跨场景恢复收益。

从保存的逐样本预测独立重算 accuracy、balanced accuracy、failure AUROC/AUPRC，与运行输出最大差为 0。完整模型本机推理约 10.18 秒，峰值已分配显存 14,070,218,752 字节；该计时不含完整加载与数据准备，不进入严格跨方法效率主表。

作者完整模型是三路分类器与 VLM 的加权投票；返回的票数比例不是校准概率。该静态图像检测任务不是 SAFE 白盒时序检测，也不是具身策略成功率，不能直接混排。

公开训练代码包含用 AHA/DROID 测试资源作模型选择验证的路径，另有训练内小型验证子集。未取得发布 checkpoint 的完整训练日志前，不把本次结果写成所有目标域都“完全未见”的 OOD 保证。本次使用作者 validation 派生测试，而非自行构建的未触碰主测试集。

数据不具有任意重置物理状态和主动换视角反事实；该对照可验证任务条件图像判断能力，不能单独证明预算路由或失败恢复收益。

## 执行与证据

组件入口：`scripts/eval_ifailsense_vlm_component.py`。完整模型入口：`scripts/eval_ifailsense_fixed.py`。后者使用安全的 tensor/state_dict 加载并严格核对键和形状，不改变分类器参数。异常推理直接停止，不静默跳过样本。

原始输出位于服务器 `/root/autodl-tmp/experiments/baselines-20260905/ifailsense-vlm-component-v1/`；[组件逐样本结果与配置](results/20260905/ifailsense-vlm-component-v1/metrics.json)进入 Git，原始图像和权重不上传。

完整模型原始输出位于同级 `ifailsense-calvin1p-v1/`；[完整指标](results/20260905/ifailsense-calvin1p-v1/metrics.json)、[配对与重算审计](results/20260905/ifailsense_paired_audit.json)进入 Git。核对入口为 `scripts/export_ifailsense_results.py`。上传及校验完成后，本地临时压缩包与下载分块已按用户要求删除；服务器权重保留。
