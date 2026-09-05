"""Export only complete independent evaluations with split and calibration audits."""
import json
import shutil
import subprocess
import hashlib
import platform
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
DEST=ROOT/'docs/reproduction/results/20260905/safe-droid-v1'
DEST.mkdir(parents=True,exist_ok=True)
records=[]; conformal=[]
raw_audit=json.loads(Path('/root/autodl-tmp/datasets/safe-rollouts/droid-extracted-v1/raw_metadata_audit.json').read_text())
flagged={r['path'].replace('meta.pkl','external_left.mp4') for r in raw_audit['label_issues']}
for model in ['lstm','indep']:
    for seed in range(3):
        source=Path(f'/root/autodl-tmp/experiments/baselines-20260905/safe-droid-v1-{model}-seed{seed}')
        metrics=json.loads((source/'final_metrics.json').read_text())
        if metrics['epoch']!=1000: raise ValueError('Incomplete epoch budget')
        splits=json.loads((source/'splits.json').read_text())
        tasks={k:{r['task_id'] for r in rows} for k,rows in splits.items()}
        paths={k:{r['path'] for r in rows} for k,rows in splits.items()}
        if tasks['train'] & tasks['val_unseen']: raise ValueError('Task leakage')
        names=list(paths)
        if any(paths[names[i]]&paths[names[j]] for i in range(len(names)) for j in range(i)): raise ValueError('Trajectory leakage')
        record=dict(model=model,seed=seed,metrics=metrics,splits={k:dict(episodes=len(rows),successes=sum(r['success'] for r in rows),failures=sum(not r['success'] for r in rows),tasks=sorted(tasks[k]),flagged_labels=sum(r['path'] in flagged for r in rows)) for k,rows in splits.items()})
        records.append(record)
        table=json.loads((source/'classify_cp_maxsofar__model.json').read_text())
        for values in table['data']:
            item=dict(zip(table['columns'],values))
            if abs(item['alpha']-.1)<1e-8 and item['calib on']=='neg' and item['task']=='all' and item['time']=='at earliest stop':
                conformal.append(dict(model=model,seed=seed,**item))
        target=DEST/source.name; target.mkdir(exist_ok=True)
        for path in source.iterdir():
            if path.suffix in {'.json','.jsonl','.csv','.yaml'}: shutil.copy2(path,target/path.name)
aggregates={}
for model in ['lstm','indep']:
    runs=[r for r in records if r['model']==model]
    aggregates[model]={key:dict(mean=float(np.mean([r['metrics'][key] for r in runs])),sample_std=float(np.std([r['metrics'][key] for r in runs],ddof=1))) for key in runs[0]['metrics'] if 'roc_auc/model_val_' in key or 'prc_auc/model_val_' in key}
summary=dict(runs=records,aggregates=aggregates,scope='Official balanced/full-length 0510 protocol; not original natural success prevalence; no cross-policy transfer claim',data_archive_sha256='5dbf96099a2bc5d4bb23c6a58e028822c62288d4691e2f8ab1dcd7ed223f51d1')
summary['raw_data_audit']={k:v for k,v in raw_audit.items() if k!='records'}
summary['provenance']=dict(python=platform.python_version(),numpy=np.__version__,
    safe_commit=subprocess.check_output(['git','-C',str(ROOT/'third_party/SAFE'),'rev-parse','HEAD'],text=True).strip(),
    scripts={name:hashlib.sha256((ROOT/'scripts'/name).read_bytes()).hexdigest() for name in ['safe_logged_train.py','run_safe_droid_matrix.sh','eval_saved_safe.py','export_safe_droid.py']})
(DEST/'summary.json').write_text(json.dumps(summary,indent=2)); (DEST/'conformal_alpha01.json').write_text(json.dumps(conformal,indent=2))
print(json.dumps(dict(aggregates=aggregates,conformal=conformal),indent=2))
