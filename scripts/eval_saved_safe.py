"""Re-evaluate each final SAFE checkpoint with upstream metrics and audited splits."""
import json
import argparse
import os
import sys
from pathlib import Path
os.environ["WANDB_MODE"] = "disabled"
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "third_party/SAFE"))
import numpy as np
import torch
import wandb
from omegaconf import OmegaConf
from torch.utils.data import DataLoader
from failure_prob.data import load_rollouts, split_rollouts
from failure_prob.data.utils import RolloutDataset
from failure_prob.model import get_model
from failure_prob.utils.random import seed_everything
from failure_prob.utils.routines import eval_model_and_log, model_forward_dataloader
from failure_prob.utils.constants import EVAL_TIME_QUANTILES

parser=argparse.ArgumentParser()
parser.add_argument("--run-prefix",default="/root/autodl-tmp/experiments/baselines-20260905/safe-v2")
parser.add_argument("--exclude-label-audit",help="Optional post-hoc sensitivity report; never changes the official checkpoint or primary results")
args=parser.parse_args()
excluded=set()
if args.exclude_label_audit:
    excluded={r["path"].replace("meta.pkl","external_left.mp4") for r in json.loads(Path(args.exclude_label_audit).read_text())["label_issues"]}
wandb.init(mode="disabled")
for model_name in ("lstm", "indep"):
    for seed in range(3):
        out = Path(f"{args.run_prefix}-{model_name}-seed{seed}")
        if not (out / "completed.json").exists():
            raise RuntimeError(f"Training not finished: {out}")
        cfg = OmegaConf.load(out / "config.yaml")
        seed_everything(0)
        all_rollouts = load_rollouts(cfg)
        seed_everything(seed)
        splits = split_rollouts(cfg, all_rollouts)
        recorded = json.loads((out / "splits.json").read_text())
        assert {k:[r.mp4_path for r in v] for k,v in splits.items()} == {k:[r["path"] for r in v] for k,v in recorded.items()}
        datasets = {k:RolloutDataset(cfg, v) for k,v in splits.items()}
        loaders = {k:DataLoader(v, batch_size=64, shuffle=False) for k,v in datasets.items()}
        model = get_model(cfg, splits["train"][0].hidden_states.shape[-1])
        model.to("cuda")  # SAFE overrides .to() to maintain its get_device() value.
        model.load_state_dict(torch.load(out / "model_final.ckpt", map_location="cuda", weights_only=True))
        model.eval()
        metrics = eval_model_and_log(cfg, model, splits, loaders, EVAL_TIME_QUANTILES[cfg.dataset.name],
                                     plot_auc_curves=False, plot_score_curves=False, log_classification_metrics=True)
        scalars = {"epoch":int(cfg.model.n_epochs)}
        for key,value in metrics.items():
            if isinstance(value, (int,float,np.number)):
                scalars[key] = value.item() if isinstance(value,np.number) else value
            elif isinstance(value,wandb.Table):
                (out / (key.replace("/","__") + ".json")).write_text(json.dumps(dict(columns=value.columns,data=value.data),default=str))
        with torch.no_grad():
            for split, loader in loaders.items():
                scores,masks,labels = model_forward_dataloader(model,loader)
                np.savez_compressed(out / f"scores_{split}.npz", scores=scores.cpu().numpy(), valid_masks=masks.cpu().numpy(), success_labels=labels.cpu().numpy())
        (out / "final_metrics.json").write_text(json.dumps(scalars,indent=2))
        print(out.name, {k:v for k,v in scalars.items() if "roc_auc/model_val_unseen" in k or "prc_auc/model_val_unseen" in k}, flush=True)
        if args.exclude_label_audit:
            clean_splits={k:[r for r in v if r.mp4_path not in excluded] for k,v in splits.items()}
            clean_loaders={k:DataLoader(RolloutDataset(cfg,v),batch_size=64,shuffle=False) for k,v in clean_splits.items()}
            sensitivity=eval_model_and_log(cfg,model,clean_splits,clean_loaders,EVAL_TIME_QUANTILES[cfg.dataset.name],
                plot_auc_curves=False,plot_score_curves=False,log_classification_metrics=True)
            numbers={k:v.item() if isinstance(v,np.number) else v for k,v in sensitivity.items() if isinstance(v,(int,float,np.number))}
            removed={k:[r.mp4_path for r in v if r.mp4_path in excluded] for k,v in splits.items()}
            for key,value in sensitivity.items():
                if isinstance(value,wandb.Table):
                    (out / ("sensitivity__"+key.replace("/","__")+".json")).write_text(json.dumps(dict(columns=value.columns,data=value.data),default=str))
            (out/"sensitivity_excluding_label_issues.json").write_text(json.dumps(dict(metrics=numbers,removed=removed,
                caveat="Same checkpoint trained on official data. Only evaluation/calibration subsets exclude flagged records; this is not clean-data retraining or label correction."),indent=2))
            del clean_splits,clean_loaders,sensitivity
        del model, datasets, loaders, splits, all_rollouts
        torch.cuda.empty_cache()
