"""Validate RGB-D and privileged-label availability, not policy success metrics."""
import json
import os
from pathlib import Path
os.environ.setdefault("MS_ASSET_DIR", "/root/autodl-tmp/datasets/maniskill3/assets")
os.environ.setdefault("MS_SKIP_ASSET_DOWNLOAD_PROMPT", "1")
import gymnasium as gym
import mani_skill.envs
import numpy as np
import torch
import imageio.v2 as imageio

out = Path("/root/autodl-tmp/experiments/baselines-20260905/maniskill3-smoke")
out.mkdir(parents=True, exist_ok=True)
rows = []
for task in ("PickCube-v1", "StackCube-v1", "PegInsertionSide-v1"):
    env = gym.make(task, obs_mode="rgb+depth", sim_backend="cpu", render_mode="rgb_array", control_mode="pd_joint_pos")
    try:
        obs, info = env.reset(seed=7)
        sensors = {}
        for camera, values in obs["sensor_data"].items():
            sensors[camera] = {k:list(v.shape) for k,v in values.items()}
            imageio.imwrite(out / f"{task}_{camera}.png", values["rgb"][0].cpu().numpy())
            assert torch.isfinite(values["depth"]).all()
        for _ in range(5):
            obs, reward, terminated, truncated, info = env.step(env.action_space.sample())
        state = env.unwrapped.get_state_dict()
        rows.append(dict(task=task, seed=7, sensors=sensors, info_fields=sorted(info), state_fields=sorted(state),
                         purpose="RGB-D/environment-label engineering smoke test, not baseline success-rate evaluation"))
        print(json.dumps(rows[-1]), flush=True)
    finally:
        env.close()
(out / "summary.json").write_text(json.dumps(rows, indent=2))
