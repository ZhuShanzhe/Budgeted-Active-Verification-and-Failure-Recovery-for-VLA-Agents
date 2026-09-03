#!/usr/bin/env python3
"""Small, deterministic dependency and GPU diagnostic for each baseline profile."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path


def module_info(name: str) -> dict[str, str | bool]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # diagnostic should report every failure together
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "ok": True,
        "version": str(getattr(module, "__version__", "unknown")),
        "path": str(getattr(module, "__file__", "namespace")),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", choices=("openvla", "ava", "safe"), required=True)
    args = parser.parse_args()

    import torch

    report: dict[str, object] = {
        "profile": args.profile,
        "python": sys.version.split()[0],
        "executable": sys.executable,
        "cwd": str(Path.cwd()),
        "cuda_available": torch.cuda.is_available(),
        "torch": torch.__version__,
        "torch_cuda": torch.version.cuda,
        "gpu": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
        "environment": {
            key: os.environ.get(key)
            for key in ("HF_HOME", "TORCH_HOME", "MUJOCO_GL", "PYOPENGL_PLATFORM", "LIBERO_CONFIG_PATH")
        },
    }

    modules = ["torch", "numpy"]
    if args.profile in {"openvla", "ava"}:
        modules += ["transformers", "prismatic", "libero.libero", "robosuite", "mujoco"]
    else:
        modules += ["failure_prob", "hydra", "sklearn"]

    report["modules"] = {name: module_info(name) for name in modules}
    print(json.dumps(report, indent=2, ensure_ascii=False))

    failed = [name for name, result in report["modules"].items() if not result["ok"]]  # type: ignore[index,union-attr]
    if not report["cuda_available"] or failed:
        print(f"FAILED: cuda={report['cuda_available']}, modules={failed}", file=sys.stderr)
        return 1
    print("DOCTOR_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
