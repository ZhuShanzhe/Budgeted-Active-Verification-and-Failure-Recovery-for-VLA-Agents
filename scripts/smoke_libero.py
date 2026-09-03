#!/usr/bin/env python3
"""Create one real LIBERO EGL environment and save initial camera observations."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", default="libero_spatial")
    parser.add_argument("--task-id", type=int, default=0)
    parser.add_argument("--output", type=Path, default=Path("outputs/smoke_libero"))
    args = parser.parse_args()

    from libero.libero import benchmark
    from libero.libero.envs import OffScreenRenderEnv

    suite = benchmark.get_benchmark_dict()[args.suite]()
    task_path = suite.get_task_bddl_file_path(args.task_id)
    env = OffScreenRenderEnv(
        bddl_file_name=task_path,
        camera_heights=128,
        camera_widths=128,
        render_gpu_device_id=0,
    )
    try:
        obs = env.reset()
        args.output.mkdir(parents=True, exist_ok=True)
        written: list[str] = []
        for key, value in obs.items():
            if "image" not in key or not isinstance(value, np.ndarray) or value.ndim != 3:
                continue
            image = np.flipud(value).astype(np.uint8)
            path = args.output / f"{args.suite}_task{args.task_id}_{key}.png"
            Image.fromarray(image).save(path)
            written.append(str(path))
        if not written:
            raise RuntimeError(f"No image observation found. Keys: {sorted(obs)}")
        print("LIBERO_RENDER_OK")
        print("\n".join(written))
    finally:
        env.close()


if __name__ == "__main__":
    main()
