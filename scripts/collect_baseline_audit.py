"""Export compact, evidence-backed results; never include incomplete runs as scores."""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import numpy as np

root = Path(__file__).resolve().parents[1]
exp = Path("/root/autodl-tmp/experiments/baselines-20260905")
dest = root / "docs/reproduction/results/20260905"
dest.mkdir(parents=True, exist_ok=True)
records = []
conformal = []
for model in ("lstm", "indep"):
    for seed in range(3):
        run = exp / f"safe-v2-{model}-seed{seed}"
        if not (run / "final_metrics.json").exists():
            print(f"INCOMPLETE {run.name}")
            continue
        last = json.loads((run / "final_metrics.json").read_text())
        assert last["epoch"] == 1000
        splits = json.loads((run / "splits.json").read_text())
        train_tasks = {r["task_id"] for r in splits["train"]}
        unseen_tasks = {r["task_id"] for r in splits["val_unseen"]}
        assert train_tasks.isdisjoint(unseen_tasks)
        sets = [{r["path"] for r in rs} for rs in splits.values()]
        assert all(sets[i].isdisjoint(sets[j]) for i in range(len(sets)) for j in range(i))
        record = dict(model=model, seed=seed, metrics=last,
                      splits={k: dict(episodes=len(v), failures=sum(not r["success"] for r in v),
                                      tasks=sorted({r["task_id"] for r in v})) for k,v in splits.items()})
        records.append(record)
        table = json.loads((run / "classify_cp_maxsofar__model.json").read_text())
        for values in table["data"]:
            entry = dict(zip(table["columns"],values))
            if abs(entry["alpha"]-0.1)<1e-8 and entry["calib on"]=="neg" and entry["task"]=="all" and entry["time"]=="at earliest stop":
                conformal.append(dict(model=model, seed=seed, **entry))
        run_dest = dest / run.name
        run_dest.mkdir(exist_ok=True)
        for f in run.iterdir():
            if f.suffix in (".json", ".jsonl", ".csv", ".yaml"):
                shutil.copy2(f, run_dest / f.name)
        print(run.name, {k:round(v,5) for k,v in last.items()
              if k in ("falert_early_roc_auc/model_val_unseen", "falert_end_roc_auc/model_val_unseen",
                       "falert_early_prc_auc/model_val_unseen", "falert_end_prc_auc/model_val_unseen")})
aggregates = {}
for model in ("lstm", "indep"):
    runs = [r for r in records if r["model"] == model]
    if len(runs) == 3:
        aggregates[model] = {k: {"mean":float(np.mean([r["metrics"][k] for r in runs])),
                                 "sample_std":float(np.std([r["metrics"][k] for r in runs], ddof=1))}
                             for k in runs[0]["metrics"] if "roc_auc/model_val_" in k or "prc_auc/model_val_" in k}
(dest / "safe_summary.json").write_text(json.dumps(dict(runs=records, aggregates=aggregates), indent=2))
(dest / "safe_conformal_alpha01.json").write_text(json.dumps(conformal,indent=2))
print("CALIBRATION", [{k:r[k] for k in ("model","seed","fpr","tpr")} for r in conformal])
for name in ("maniskill3-smoke", "failgen-smoke"):
    run = exp / name
    target = dest / name
    target.mkdir(exist_ok=True)
    for filename in ("summary.json", "attempts.jsonl"):
        if (run / filename).exists():
            shutil.copy2(run / filename, target / filename)
replays = []
for path in sorted((exp / "maniskill-replay").rglob("*.json")):
    if path.is_symlink():
        continue
    data = json.loads(path.read_text())
    replays.append(dict(task=path.parent.name, metadata_path=str(path), episodes=data["episodes"]))
(dest / "maniskill_replay_summary.json").write_text(json.dumps(replays,indent=2))
for name in ("oft-clean-spatial-50", "ava-clean-spatial-50", "oft-plus-spatial-70", "ava-plus-spatial-70"):
    run = exp / name
    if not (run / "summary.json").exists():
        print(f"INCOMPLETE {name}")
        continue
    target = dest / name
    target.mkdir(exist_ok=True)
    for f in run.iterdir():
        if f.suffix in (".json", ".jsonl"):
            shutil.copy2(f, target / f.name)
    print(name, (run / "summary.json").read_text())
versions = {}
for name in ("SAFE", "WCM", "openvla-oft", "AVA-VLA", "LIBERO-original", "LIBERO-plus", "maniskill-failgen"):
    path = root / "third_party" / name
    if (path / ".git").exists():
        versions[name] = subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()
(dest / "source_commits.json").write_text(json.dumps(versions, indent=2))
print("EXPORTED", dest)
