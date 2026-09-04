# LIBERO-Plus

- **状态：L2 环境链路复现。**
- 官方资产压缩包约 6.4 GB，解压后约 16 GB，已安装在 `/root/autodl-tmp/datasets/LIBERO-plus-assets`。
- 无显示器 EGL 环境可创建；agent-view 与 wrist-view 两路相机均完成渲染。
- LeRobot 训练/评测数据约 16 GB，下载路径为 `/root/autodl-tmp/datasets/libero-plus-lerobot`。

## 可借鉴内容

七维渐进扰动构成本项目主 OOD 协议。报告不只给平均成功率，还给每一扰动轴的失效边界、critic 检出率、恢复成功率、平均查询成本和选择性风险。

## 尚未完成

尚未在四套任务上运行完整多种子 rollout，也未复算论文的七维鲁棒性指标。环境创建和渲染通过只能证明评测基础设施可用。

来源：https://huggingface.co/datasets/Sylvest/LIBERO-plus
