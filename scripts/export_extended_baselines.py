"""Compact publication evidence for completed supplemental baseline runs only."""
import json
from pathlib import Path
import shutil
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
source=Path('/root/autodl-tmp/experiments/baselines-20260905/safe-distance-v1')
dest=ROOT/'docs/reproduction/results/20260905/extended-baselines'
dest.mkdir(parents=True,exist_ok=True)
records=[]; calibration=[]
for domain in ['widowx','droid']:
    for distance in ['cosine','euclid']:
        for seed in range(3):
            path=source/f'{domain}-{distance}-seed{seed}'
            meta=json.loads((path/'completed.json').read_text())
            if meta['status']!='complete': raise ValueError(path)
            metrics=json.loads((path/'final_metrics.json').read_text())
            records.append(dict(domain=domain,method=distance,seed=seed,metrics=metrics,provenance=meta))
            for row in json.loads((path/'conformal.json').read_text()):
                if abs(float(row['alpha'])-.1)<1e-8 and row['calib on']=='neg' and row['task']=='all' and row['time'] in ['at earliest stop','by earliest stop']:
                    calibration.append(dict(domain=domain,method=distance,seed=seed,**row))
            target=dest/path.name; target.mkdir(exist_ok=True)
            for artifact in path.iterdir():
                if artifact.suffix in {'.json','.yaml'}: shutil.copy2(artifact,target/artifact.name)
aggregates={}
for domain in ['widowx','droid']:
    aggregates[domain]={}
    for method in ['cosine','euclid']:
        selected=[r for r in records if r['domain']==domain and r['method']==method]
        aggregates[domain][method]={}
        for name in ['falert_early_roc_auc/model_val_unseen','falert_early_prc_auc/model_val_unseen','roc_auc/model_val_unseen_tq0.5']:
            values=[r['metrics'][name] for r in selected]
            aggregates[domain][method][name]=dict(mean=float(np.mean(values)),sample_std=float(np.std(values,ddof=1)))
summary=dict(runs=records,aggregates=aggregates,conformal_alpha01=calibration,
             scope='Official SAFE EmbedModel; k=5; successful and failed TRAIN bank; no cumsum; same prior splits; no hyperparameter search',
             checkpoint_storage='Train feature banks and scores NPZ remain on server; bank SHA256 in each completed record')
(dest/'summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps(dict(aggregates=aggregates,conformal=calibration),indent=2))
