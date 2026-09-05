"""Paired LIBERO evaluation using upstream episode loops and fixed initial states.

Infrastructure errors are recorded separately from policy failures. This is a
finite subset protocol, not a claim to reproduce all published benchmark scores.
"""
import argparse
import dataclasses
import io
import json
import os
import subprocess
import sys
import time
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("--policy", choices=["oft", "ava"], required=True)
p.add_argument("--trials", type=int, default=5)
p.add_argument("--seed", type=int, default=7)
p.add_argument("--benchmark", choices=["clean", "plus"], default="clean")
p.add_argument("--output", required=True)
a = p.parse_args()
root = Path(__file__).resolve().parents[1]
source = root / "third_party" / ("openvla-oft" if a.policy == "oft" else "AVA-VLA")
sys.path.insert(0, str(source))
libero_source = root / "third_party" / ("LIBERO-original" if a.benchmark == "clean" else "LIBERO-plus")
sys.path.insert(0, str(libero_source))
out = Path(a.output)
out.mkdir(parents=True, exist_ok=True)
if (out / "episodes.jsonl").exists():
    raise FileExistsError("Use a fresh output directory; existing results are immutable")
config_dir = out / "libero-config"
config_dir.mkdir(exist_ok=True)
libero_root = libero_source / "libero/libero"
import yaml
(config_dir / "config.yaml").write_text(yaml.safe_dump({
    "benchmark_root": str(libero_root), "bddl_files": str(libero_root / "bddl_files"),
    "init_states": str(libero_root / "init_files"), "assets": str(libero_root / "assets"),
    "datasets": "/root/autodl-tmp/datasets/LIBERO-original"}))
os.environ["LIBERO_CONFIG_PATH"] = str(config_dir)
os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
# Only released LIBERO initial-state files and released model weights are loaded.
os.environ["TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD"] = "1"
import numpy as np
import torch
from libero.libero import benchmark
from experiments.robot.libero import run_libero_eval as upstream
from experiments.robot.libero.libero_utils import get_libero_env
from experiments.robot.robot_utils import set_seed_everywhere, get_image_resize_size

cfg = upstream.GenerateConfig(
    pretrained_checkpoint="/root/autodl-tmp/checkpoints/" + (
        "openvla-7b-oft-libero-spatial" if a.policy == "oft" else "avavla-libero-4in1"),
    task_suite_name="libero_spatial", num_trials_per_task=a.trials,
    seed=a.seed, env_img_res=256, num_open_loop_steps=8,
    use_l1_regression=True, use_diffusion=False, use_film=False,
    num_images_in_input=2, use_proprio=True, center_crop=True,
    local_log_dir=str(out),
)
if a.policy == "ava":
    cfg.multi_frame = upstream.MultiFrameConfig(
        temporal_strategy="attn_weight", temporal_feature_source="action",
        temporal_feature_layer=-2, attn_weight_force_eager_attn=True,
        attn_weight_extra_layer_ids="(i for i in range(0, 32))",
        attn_weight_head_type="softmaxscore", attn_weight_score_config="(1.9, 0.1, 0.0)",
        attn_weight_sink_ids=[68, 75, 180, 187, 324, 331, 436, 443],
        attn_weight_sink_weight=1.0)
set_seed_everywhere(a.seed)
if a.policy == "oft":
    from experiments.robot.openvla_utils import get_vla, get_action_head, get_processor, get_proprio_projector
    processor = get_processor(upstream.GenerateConfig(pretrained_checkpoint="moojink/openvla-7b-oft-finetuned-libero-spatial"))
    cfg.unnorm_key = "libero_spatial_no_noops"
    model = get_vla(cfg)
    action_head = get_action_head(cfg, model.llm_dim)
    proprio = get_proprio_projector(cfg, model.llm_dim, proprio_dim=8)
    noisy = None
else:
    model, action_head, proprio, noisy, attention, processor = upstream.initialize_model(cfg)

manifest = dict(policy=a.policy, config=dataclasses.asdict(cfg), protocol="spatial-first-N-official-initial-states",
                upstream_commit=subprocess.check_output(["git", "-C", str(source), "rev-parse", "HEAD"], text=True).strip(),
                torch=torch.__version__, gpu=torch.cuda.get_device_name(), paired_initial_states=True)
(out / "config.json").write_text(json.dumps(manifest, indent=2, default=str))
suite = benchmark.get_benchmark_dict()["libero_spatial"]()
assert suite.n_tasks == (10 if a.benchmark == "clean" else 2402), f"Unexpected task suite size {suite.n_tasks}"
assert Path(benchmark.__file__).resolve().is_relative_to(libero_source.resolve())
if a.benchmark == "clean":
    selected = [dict(task_id=i, category="clean") for i in range(10)]
else:
    assert a.trials == 1, "LIBERO-Plus uses one initial state per perturbed task"
    import random
    classification = json.loads((libero_source / "libero/libero/benchmark/task_classification.json").read_text())["libero_spatial"]
    rng = random.Random(20260905)
    selected = []
    for category in sorted({x["category"] for x in classification}):
        group = sorted((x for x in classification if x["category"] == category), key=lambda x:x["name"])
        for item in rng.sample(group, 10):
            task_id = item["id"] - 1
            assert suite.get_task(task_id).name == item["name"]
            selected.append(dict(task_id=task_id, category=category, difficulty_level=item["difficulty_level"], name=item["name"]))
    assert len(selected) == 70
(out / "task_selection.json").write_text(json.dumps(selected, indent=2))
manifest["benchmark"] = a.benchmark
manifest["libero_commit"] = subprocess.check_output(["git", "-C", str(libero_source), "rev-parse", "HEAD"], text=True).strip()
manifest["protocol"] = "clean-10tasks-first-N-states" if a.benchmark == "clean" else "plus-stratified-10-per-category-seed20260905"
(out / "config.json").write_text(json.dumps(manifest, indent=2, default=str))
original_action = upstream.get_action
latencies = []

def timed_action(*args, **kwargs):
    torch.cuda.synchronize()
    start = time.perf_counter()
    result = original_action(*args, **kwargs)
    torch.cuda.synchronize()
    latencies.append(time.perf_counter() - start)
    return result

upstream.get_action = timed_action
rows = []
for selected_task in selected:
    task_id = selected_task["task_id"]
    task = suite.get_task(task_id)
    states = suite.get_task_init_states(task_id)
    env, description = get_libero_env(task, cfg.model_family, resolution=cfg.env_img_res)
    try:
        for ep in range(a.trials):
            latencies.clear()
            log = io.StringIO()
            start = time.perf_counter()
            kwargs = dict(processor=processor, action_head=action_head, proprio_projector=proprio,
                          noisy_action_projector=noisy, initial_state=states[ep], log_file=log)
            if a.policy == "ava":
                kwargs.update(vision_attn_weight_generator=attention)
            result = upstream.run_episode(cfg, env, description, model, get_image_resize_size(cfg), **kwargs)
            error = log.getvalue() if "Episode error:" in log.getvalue() else None
            row = dict(task_id=task_id, category=selected_task["category"], task=description, initial_state_index=ep, seed=a.seed,
                       success=bool(result[0]), infrastructure_error=error, steps=len(result[1]),
                       seconds=time.perf_counter()-start, policy_queries=len(latencies),
                       inference_seconds=sum(latencies), query_latencies=list(latencies))
            rows.append(row)
            with (out / "episodes.jsonl").open("a") as f:
                f.write(json.dumps(row) + "\n")
            print(json.dumps({k:v for k,v in row.items() if k != "query_latencies"}), flush=True)
            if ep == 0 and result[1]:
                import imageio.v2 as imageio
                imageio.mimsave(out / f"task{task_id}_ep0.mp4", result[1], fps=20)
            if error:
                raise RuntimeError(error)
    finally:
        env.close()
n = len(rows)
s = sum(r["success"] for r in rows)
z = 1.959963984540054
den = 1 + z*z/n
center = (s/n + z*z/(2*n))/den
half = z*((s/n*(1-s/n)/n + z*z/(4*n*n))**0.5)/den
summary = dict(episodes=n, successes=s, success_rate=s/n,
               wilson95=[center-half, center+half], seed=a.seed,
               total_policy_queries=sum(r["policy_queries"] for r in rows),
               total_inference_seconds=sum(r["inference_seconds"] for r in rows),
               total_episode_seconds=sum(r["seconds"] for r in rows),
               peak_cuda_memory_gb=torch.cuda.max_memory_allocated()/1e9,
               per_task={str(t["task_id"]):sum(r["success"] for r in rows if r["task_id"]==t["task_id"])/a.trials for t in selected},
               per_category={c:dict(successes=sum(r["success"] for r in rows if r["category"]==c), episodes=sum(r["category"]==c for r in rows)) for c in sorted({r["category"] for r in rows})},
               limitation="Single seed, first N initial states per task; no full 50-trial published-score claim. Wilson interval is descriptive; episodes cluster by task.")
(out / "summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary), flush=True)
