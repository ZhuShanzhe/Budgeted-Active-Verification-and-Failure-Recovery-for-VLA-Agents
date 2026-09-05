"""Export all six completed RND runs; incomplete runs are never summarized."""
import hashlib
import json
from pathlib import Path
import shutil
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path('/root/autodl-tmp/experiments/baselines-20260905/safe-rnd-v1')
DEST = ROOT / 'docs/reproduction/results/20260905/safe-rnd-v1'


def main():
    runs = []
    cp = []
    # Validate complete matrix before producing a publication summary.
    for domain in ['widowx', 'droid']:
        for seed in range(3):
            path = SOURCE / f'{domain}-seed{seed}'
            record = json.loads((path / 'completed.json').read_text())
            assert record['status'] == 'complete' and record['epochs'] == 200
            assert record['reload_probe_max_error'] <= 1e-6
            logs = [json.loads(line) for line in (path / 'training.jsonl').read_text().splitlines()]
            assert len(logs) == 200 and all(np.isfinite(x['loss']) for x in logs)
            digest = hashlib.sha256()
            with (path / 'model_final.ckpt').open('rb') as stream:
                for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                    digest.update(chunk)
            runs.append(dict(domain=domain, seed=seed, provenance=record,
                             checkpoint_sha256=digest.hexdigest(),
                             metrics=json.loads((path / 'final_metrics.json').read_text())))
            for row in json.loads((path / 'conformal.json').read_text()):
                if abs(float(row['alpha']) - .1) < 1e-8 and row['calib on'] == 'neg' and row['task'] == 'all' and row['time'] in ['at earliest stop', 'by earliest stop']:
                    cp.append(dict(domain=domain, seed=seed, **row))
    DEST.mkdir(parents=True, exist_ok=True)
    for run in runs:
        path = SOURCE / f"{run['domain']}-seed{run['seed']}"
        target = DEST / path.name
        target.mkdir(exist_ok=True)
        for artifact in path.iterdir():
            if artifact.suffix in {'.json', '.yaml', '.jsonl'}:
                shutil.copy2(artifact, target / artifact.name)
    aggregates = {}
    for domain in ['widowx', 'droid']:
        aggregates[domain] = {}
        for key in ['falert_early_roc_auc/model_val_unseen', 'falert_early_prc_auc/model_val_unseen', 'roc_auc/model_val_unseen_tq0.5', 'roc_auc/model_val_unseen_tq1.0']:
            values = [r['metrics'][key] for r in runs if r['domain'] == domain]
            aggregates[domain][key] = dict(mean=float(np.mean(values)), sample_std=float(np.std(values, ddof=1)))
    summary = dict(runs=runs, aggregates=aggregates, conformal_alpha01=cp,
                   scope='Official SAFE RND network/loss; 200 epochs, nominal batch 32, merged tails, exact prior splits. No test-based checkpoint or hyperparameter selection.',
                   verification='Every final checkpoint reloaded; first val_seen trajectory compared with pre-save prediction, then full split evaluation performed from reloaded checkpoint. Not a second independent full prediction run.')
    (DEST / 'summary.json').write_text(json.dumps(summary, indent=2))
    print(json.dumps(dict(aggregates=aggregates, cp=cp), indent=2))


if __name__ == '__main__':
    main()
