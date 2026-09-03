#!/usr/bin/env python3
"""Run one real LIBERO observation through a released OpenVLA-OFT checkpoint."""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--checkpoint",
        default="/root/autodl-tmp/checkpoints/openvla-7b-oft-libero-spatial",
    )
    parser.add_argument(
        "--processor-checkpoint",
        default="moojink/openvla-7b-oft-finetuned-libero-spatial",
        help="Hub ID used only for the processor; avoids the released local-path auto-map mutation.",
    )
    parser.add_argument("--task-id", type=int, default=0)
    parser.add_argument("--seed", type=int, default=7)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    source_root = repo_root / "third_party" / "openvla-oft"
    sys.path.insert(0, str(source_root))

    from libero.libero import benchmark
    from experiments.robot.libero.libero_utils import get_libero_dummy_action, get_libero_env
    from experiments.robot.libero.run_libero_eval import GenerateConfig, prepare_observation
    from experiments.robot.openvla_utils import (
        get_action_head,
        get_processor,
        get_proprio_projector,
        get_vla,
    )
    from experiments.robot.robot_utils import get_action, get_image_resize_size, set_seed_everywhere
    from prismatic.vla.constants import NUM_ACTIONS_CHUNK

    cfg = GenerateConfig(
        pretrained_checkpoint=args.checkpoint,
        task_suite_name="libero_spatial",
        use_l1_regression=True,
        use_diffusion=False,
        use_film=False,
        num_images_in_input=2,
        use_proprio=True,
        center_crop=True,
        num_open_loop_steps=NUM_ACTIONS_CHUNK,
        unnorm_key="libero_spatial_no_noops",
        seed=args.seed,
    )
    set_seed_everywhere(cfg.seed)

    # The released loader mutates a local model's config auto-map before loading
    # the processor. Load the identical released processor from its Hub ID first,
    # then keep all large policy and head weights on the local data disk.
    processor_cfg = GenerateConfig(pretrained_checkpoint=args.processor_checkpoint)
    processor = get_processor(processor_cfg)
    started = time.perf_counter()
    model = get_vla(cfg)
    action_head = get_action_head(cfg, model.llm_dim)
    proprio_projector = get_proprio_projector(cfg, model.llm_dim, proprio_dim=8)
    noisy_action_projector = None
    load_seconds = time.perf_counter() - started

    suite = benchmark.get_benchmark_dict()[cfg.task_suite_name]()
    task = suite.get_task(args.task_id)
    env, task_description = get_libero_env(task, cfg.model_family, resolution=cfg.env_img_res)
    try:
        obs = env.reset()
        # A smoke test only needs a genuine simulator observation. Full benchmark
        # runs use the released fixed initial states after explicitly opting in to
        # PyTorch's legacy trusted-pickle loader for the official LIBERO files.
        for _ in range(cfg.num_steps_wait):
            obs, _, _, _ = env.step(get_libero_dummy_action(cfg.model_family))

        observation, _ = prepare_observation(obs, get_image_resize_size(cfg))
        started = time.perf_counter()
        actions = get_action(
            cfg,
            model,
            observation,
            task_description,
            processor=processor,
            action_head=action_head,
            proprio_projector=proprio_projector,
            noisy_action_projector=noisy_action_projector,
            use_film=cfg.use_film,
        )
        forward_seconds = time.perf_counter() - started
    finally:
        env.close()

    actions = np.asarray(actions)
    if actions.shape != (NUM_ACTIONS_CHUNK, 7):
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
    print("OPENVLA_OFT_FORWARD_OK")


if __name__ == "__main__":
    main()
