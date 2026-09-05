"""Run the unchanged SAFE training entry with local metrics/split audit hooks.

Pass official Hydra overrides on the command line. W&B is disabled; no upload.
One seed per process avoids overwriting the upstream final checkpoint across seeds.
"""
import json
import hashlib
import os
import sys
from pathlib import Path

os.environ["WANDB_MODE"] = "disabled"
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "third_party/SAFE"))
import numpy as np
import wandb
import failure_prob.train as training

out = Path(os.environ["SAFE_AUDIT_DIR"])
out.mkdir(parents=True, exist_ok=True)
(out / "argv.json").write_text(json.dumps(sys.argv, indent=2))
original_log = wandb.log
original_init = wandb.init
original_finish = wandb.finish
original_split = training.split_rollouts
original_load = training.load_rollouts

def capture_load(cfg):
    rollouts=original_load(cfg)
    records=[]
    for rollout in rollouts:
        features=rollout.hidden_states.detach().float().cpu().numpy()
        if features.ndim!=2 or not features.size or not np.isfinite(features).all():
            raise ValueError("Invalid feature trajectory: "+rollout.mp4_path)
        records.append(dict(path=rollout.mp4_path,task_id=str(rollout.task_id),
            task_description=rollout.task_description,success=bool(rollout.episode_success),
            feature_shape=list(features.shape),feature_sha256=hashlib.sha256(features.tobytes()).hexdigest(),
            referenced_video_exists=Path(rollout.mp4_path).is_file()))
    (out/"input_audit.json").write_text(json.dumps(dict(dataset=cfg.dataset.name,loaded_after_official_filters=len(records),
        unique_tasks=len({r["task_id"] for r in records}),successes=sum(r["success"] for r in records),
        failures=sum(not r["success"] for r in records),records=records),indent=2))
    return rollouts

def capture_log(data, *args, **kwargs):
    scalars = {}
    for key, value in data.items():
        if isinstance(value, (int, float, str, bool, np.number)):
            scalars[key] = value.item() if isinstance(value, np.number) else value
        elif isinstance(value, wandb.Table):
            table_path = out / (key.replace("/", "__") + ".json")
            table_path.write_text(json.dumps(dict(columns=value.columns, data=value.data), default=str))
    with (out / "metrics.jsonl").open("a") as f:
        f.write(json.dumps(scalars, allow_nan=True) + "\n")
    return original_log(data, *args, **kwargs)

def capture_split(cfg, rollouts):
    splits = original_split(cfg, rollouts)
    records = {k: [dict(task_id=str(r.task_id), episode_idx=int(r.episode_idx),
                        success=bool(r.episode_success), path=r.mp4_path,
                        steps=int(r.hidden_states.shape[0])) for r in v]
               for k, v in splits.items()}
    (out / "splits.json").write_text(json.dumps(records, indent=2))
    return splits

wandb.log = capture_log
def capture_init(*args, **kwargs):
    global original_log
    result = original_init(*args, **kwargs)
    original_log = wandb.log  # init installs the real run logger, replacing pre-init stubs.
    wandb.log = capture_log
    return result

wandb.init = capture_init
def compatible_finish(*args, **kwargs):
    kwargs.pop("quiet", None)  # Removed in the installed W&B API; logging only.
    return original_finish(*args, **kwargs)

wandb.finish = compatible_finish
training.split_rollouts = capture_split
training.load_rollouts = capture_load
training.main()
(out / "completed.json").write_text(json.dumps({"status": "completed"}))
