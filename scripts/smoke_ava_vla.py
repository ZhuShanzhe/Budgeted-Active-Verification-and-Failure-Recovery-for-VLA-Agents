#!/usr/bin/env python3
"""Run one real LIBERO observation through the released AVA-VLA checkpoint."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import torch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--checkpoint",
        default="/root/autodl-tmp/checkpoints/avavla-libero-4in1",
    )
    parser.add_argument("--task-id", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "third_party" / "AVA-VLA"))

    from libero.libero import benchmark
    from experiments.robot.libero.libero_utils import get_libero_dummy_action, get_libero_env
    from experiments.robot.libero.run_libero_eval import (
        GenerateConfig,
        MultiFrameConfig,
        initialize_model,
        prepare_observation,
    )
    from experiments.robot.robot_utils import get_action

    cfg = GenerateConfig(pretrained_checkpoint=args.checkpoint)
    cfg.multi_frame = MultiFrameConfig(
        temporal_strategy="attn_weight",
        temporal_feature_source="action",
        temporal_feature_layer=-2,
        attn_weight_force_eager_attn=True,
        attn_weight_extra_layer_ids="(i for i in range(0, 32))",
        attn_weight_head_type="softmaxscore",
        attn_weight_score_config="(1.9, 0.1, 0.0)",
        attn_weight_sink_ids=[68, 75, 180, 187, 324, 331, 436, 443],
        attn_weight_sink_weight=1.0,
    )

    started = time.perf_counter()
    model, action_head, proprio_projector, noisy_projector, attention_head, processor = initialize_model(cfg)
    load_seconds = time.perf_counter() - started

    suite = benchmark.get_benchmark_dict()["libero_spatial"]()
    task = suite.get_task(args.task_id)
    env, task_description = get_libero_env(task, cfg.model_family, resolution=128)
    try:
        obs = env.reset()
        for _ in range(3):
            obs, _, _, _ = env.step(get_libero_dummy_action(cfg.model_family))
        observation, _, _ = prepare_observation(obs, 128)
        torch.cuda.synchronize()
        started = time.perf_counter()
        actions, _, _, _, _ = get_action(
            cfg,
            model,
            observation,
            task_description,
            processor=processor,
            action_head=action_head,
            proprio_projector=proprio_projector,
            noisy_action_projector=noisy_projector,
            use_film=False,
            temporal_context=None,
            vision_attn_weight_generator=attention_head,
        )
        torch.cuda.synchronize()
        forward_seconds = time.perf_counter() - started
    finally:
        env.close()

    actions = np.asarray(actions)
    if actions.shape != (8, 7):
        raise RuntimeError(f"unexpected action shape: {actions.shape}")
    if not np.isfinite(actions).all():
        raise RuntimeError("model returned non-finite actions")

    print(f"checkpoint={args.checkpoint}")
    print(f"task={task_description}")
    print(f"parameters={sum(parameter.numel() for parameter in model.parameters()):,}")
    print(f"model_load_seconds={load_seconds:.2f}")
    print(f"forward_seconds={forward_seconds:.3f}")
    print(f"actions_shape={actions.shape}")
    print(f"first_action={np.round(actions[0], 4).tolist()}")
    print("AVAVLA_FORWARD_OK")


if __name__ == "__main__":
    main()
