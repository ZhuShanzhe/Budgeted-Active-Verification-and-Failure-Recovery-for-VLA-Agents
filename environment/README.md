# Server environments

## Storage layout

```text
/root/autodl-tmp/conda-envs/       conda environments
/root/autodl-tmp/huggingface/      Hugging Face cache
/root/autodl-tmp/torch-cache/      PyTorch cache
/root/autodl-tmp/datasets/         external and generated datasets
/root/autodl-tmp/checkpoints/      model checkpoints
/root/autodl-tmp/experiments/      experiment outputs
/root/autodl-tmp/logs/             installation and run logs
```

## Environments

### `openvla-oft`

Contains OpenVLA-OFT, its official Transformers fork, TensorFlow/RLDS dependencies, robosuite, and LIBERO-Plus. PyTorch 2.11 + CUDA 12.8 is intentionally retained for RTX 5090 (`sm_120`) support instead of the project's historical PyTorch 2.2 pin.

### `ava-vla`

Cloned from the validated OpenVLA environment, then isolated with AVA-VLA's own Transformers fork and editable source package. It must not share a Python environment with OpenVLA-OFT because both projects patch Transformers differently.

### `vla-safe`

Contains SAFE and its detector dependencies. It is kept separate from the policy environments so calibration experiments do not disturb policy dependencies.

## Network use

```bash
# GitHub/Hugging Face only
source /etc/network_turbo

# Before pip against the configured package mirror
unset http_proxy https_proxy
```

## Environment variables

The conda environments point caches and outputs at `/root/autodl-tmp`. The VLA environments also use EGL headless rendering and the shared LIBERO configuration in `/root/autodl-tmp/libero-config`.

## Validation levels

1. `python scripts/doctor.py --profile ...` validates imports and GPU visibility.
2. `python scripts/smoke_libero.py` creates a real MuJoCo environment and saves two camera frames.
3. A one-task, one-episode checkpoint run validates model loading and action generation.
4. Full fixed-seed evaluation starts only after all previous levels pass.

The tested package versions and compatibility pins are recorded in [`VALIDATED_VERSIONS.md`](VALIDATED_VERSIONS.md).
