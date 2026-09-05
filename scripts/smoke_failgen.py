"""Bounded FailGen execution audit; injected perturbations are not failure labels."""
import json
import os
import sys
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "third_party/maniskill-failgen"))
os.environ.setdefault("MS_ASSET_DIR", "/root/autodl-tmp/datasets/maniskill3/assets")
os.environ.setdefault("MS_SKIP_ASSET_DOWNLOAD_PROMPT", "1")
import numpy as np
import torch
from omegaconf import OmegaConf
import mani_skill.examples.motionplanning.base_motionplanner.utils as planning_utils
# ManiSkill 3.0.1 moved these helpers; the algorithms are unchanged.
sys.modules["mani_skill.examples.motionplanning.panda.utils"] = planning_utils
from failgen.env_wrapper import FailgenWrapper

out = Path("/root/autodl-tmp/experiments/baselines-20260905/failgen-smoke")
out.mkdir(parents=True, exist_ok=True)
original_load = OmegaConf.load
def load_config(path):
    cfg = original_load(path)
    cfg.save_path = str(out / "generated")
    cfg.sim_backend = "cpu"
    return cfg
OmegaConf.load = load_config
np.random.seed(7)
torch.manual_seed(7)
rows = []
for task in ("FailPickCube-v1", "FailStackCube-v1"):
    wrapper = FailgenWrapper(task_name=task, headless=True, save_video=True)
    try:
        for failure_type in ("grasp", "trans_x"):
            wrapper._fail_plan_wrapper.set_active_type(failure_type)
            stage = wrapper._fail_plan_wrapper._active_fail.stages[0]
            wrapper._fail_plan_wrapper.set_active_stage(stage)
            for seed in (7, 8):
                result = wrapper._solve_fn(wrapper._env, wrapper._fail_plan_wrapper, seed=seed, debug=False, vis=False)
                if isinstance(result, tuple) and len(result) >= 5 and "success" in result[4]:
                    success = bool(result[4]["success"].item())
                    status = "completed_rollout"
                else:
                    success = None
                    status = "planner_did_not_return_rollout"
                record = dict(task=task, failure_type=failure_type, stage=int(stage), seed=seed,
                              task_success=success, status=status, result_type=type(result).__name__)
                rows.append(record)
                wrapper.save_video(save=True, ep_idx=len(rows))
                with (out / "attempts.jsonl").open("a") as f:
                    f.write(json.dumps(record) + "\n")
                print(json.dumps(record), flush=True)
    finally:
        wrapper._env.close()
(out / "summary.json").write_text(json.dumps(rows, indent=2))
