"""CPU-only independent metric audit and label sensitivity from frozen RND scores."""
import json
import os
from pathlib import Path
import sys
os.environ['WANDB_MODE'] = 'disabled'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'third_party/SAFE'))
import numpy as np
from omegaconf import OmegaConf
from failure_prob.data import load_rollouts, split_rollouts
from failure_prob.utils.random import seed_everything
from failure_prob.utils.metrics import eval_scores_roc_prc, eval_split_conformal
from failure_prob.utils.constants import EVAL_TIME_QUANTILES

BASE = Path('/root/autodl-tmp/experiments/baselines-20260905/safe-rnd-v1')
AUDIT = Path('/root/autodl-tmp/datasets/safe-rollouts/droid-extracted-v1/raw_metadata_audit.json')


def main():
    excluded = {r['path'].replace('meta.pkl', 'external_left.mp4') for r in json.loads(AUDIT.read_text())['label_issues']}
    cfg = OmegaConf.load(BASE / 'droid-seed0/config.yaml')
    seed_everything(0)
    pool = load_rollouts(cfg)
    for seed in range(3):
        path = BASE / f'droid-seed{seed}'
        assert json.loads((path / 'completed.json').read_text())['status'] == 'complete'
        cfg = OmegaConf.load(path / 'config.yaml')
        seed_everything(seed)
        splits = split_rollouts(cfg, pool)
        saved = json.loads((path / 'splits.json').read_text())
        assert {k:[r.mp4_path for r in rows] for k,rows in splits.items()} == {k:[r['path'] for r in rows] for k,rows in saved.items()}
        curves = {}
        for name, rows in splits.items():
            arrays = np.load(path / f'scores_{name}.npz', allow_pickle=False)
            lengths = arrays['valid_masks'].sum(-1).astype(int)
            assert len(lengths) == len(rows)
            curves[name] = [arrays['scores'][i, :n] for i, n in enumerate(lengths)]
        metrics = eval_scores_roc_prc(splits, curves, 'model', EVAL_TIME_QUANTILES[cfg.dataset.name], False, False)
        original = json.loads((path / 'final_metrics.json').read_text())
        differences = [abs(float(metrics[k]) - float(v)) for k,v in original.items() if np.isfinite(v)]
        assert max(differences) <= 1e-10
        kept = {name:[i for i,r in enumerate(rows) if name == 'train' or r.mp4_path not in excluded] for name, rows in splits.items()}
        clean_splits = {k:[rows[i] for i in kept[k]] for k,rows in splits.items()}
        clean_scores = {k:[rows[i] for i in kept[k]] for k,rows in curves.items()}
        result = eval_scores_roc_prc(clean_splits, clean_scores, 'model', EVAL_TIME_QUANTILES[cfg.dataset.name], False, False)
        scalars = {k:float(v) for k,v in result.items() if isinstance(v,(int,float,np.number))}
        cp = eval_split_conformal(clean_splits, clean_scores, 'model', calib_split_names=['val_seen'], test_split_names=['val_unseen'])
        record = dict(metrics=scalars, conformal=cp, independent_metric_max_error=max(differences),
                      removed={k:[r.mp4_path for i,r in enumerate(rows) if i not in kept[k]] for k,rows in splits.items()},
                      scope='Same checkpoint and saved predictions. Exclude flagged calibration/test rows only. Original task_min_step retained. Not clean-data retraining or second independent model inference.')
        (path / 'sensitivity.json').write_text(json.dumps(record, indent=2, default=str))
        print(json.dumps(dict(seed=seed, early_auroc=scalars['falert_early_roc_auc/model_val_unseen'], max_error=max(differences))), flush=True)


if __name__ == '__main__':
    main()
