# Validated server versions

Validated on the rented single-GPU server with an NVIDIA RTX 5090 (32 GB) and Ubuntu 22.04.

| Profile | Key validated versions and constraints |
| --- | --- |
| Common VLA runtime | Python 3.10, PyTorch 2.11.0+cu128, torchvision 0.26.0+cu128, torchaudio 2.11.0+cu128 |
| Simulation | MuJoCo 2.3.7, robosuite 1.4.1, BDDL 1.0.1, headless EGL |
| OpenVLA-OFT | project-specific Transformers 4.40.1 fork, TensorFlow 2.15, TFDS 4.9.3, NumPy 1.26.4, protobuf 3.20.3 |
| AVA-VLA | its own isolated Transformers 4.40.1 fork; the OpenVLA-OFT and AVA forks are intentionally not mixed |
| SAFE | isolated `vla-safe` environment with the released failure-probability package and Hydra entrypoint |

## Reproducibility constraints

- PyTorch 2.11.0+cu128 is retained because the server GPU requires `sm_120` support; historical project pins to PyTorch 2.2 are not used.
- MuJoCo is pinned to 2.3.7 because newer MuJoCo 3.x changed joint representations and breaks the released LIBERO task stack.
- `wandb` is pinned to 0.16.6 in the VLA environments to remain compatible with protobuf 3.20.3 required by the TensorFlow/RLDS stack.
- Model weights, datasets, conda environments, and experiment outputs live under `/root/autodl-tmp` and are excluded from Git.

Exact package snapshots are recorded on the server under `/root/autodl-tmp/logs` after each validated environment change.
