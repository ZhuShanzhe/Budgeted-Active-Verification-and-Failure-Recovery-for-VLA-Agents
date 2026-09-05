"""Export compact I-FailSense evidence and audit paired predictions."""
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score, balanced_accuracy_score, roc_auc_score, precision_recall_curve, auc

root = Path('/root/autodl-tmp/experiments/baselines-20260905')
dest = Path('docs/reproduction/results/20260905')
names = ['ifailsense-calvin1p-v1', 'ifailsense-vlm-component-v1']
records = []
for name in names:
    src = root / name
    assert json.loads((src / 'completed.json').read_text()) == {'status': 'complete', 'samples': 203, 'skipped': 0}
    rows = [json.loads(line) for line in (src / 'predictions.jsonl').read_text().splitlines()]
    assert len(rows) == 203 and len({r['source_row'] for r in rows}) == 203
    records.append({r['source_row']: r for r in rows})
    out = dest / name
    out.mkdir(parents=True, exist_ok=True)
    for p in src.iterdir():
        if p.suffix in {'.json', '.jsonl'}:
            assert p.stat().st_size < 5_000_000
            shutil.copy2(p, out / p.name)

full, component = records
assert full.keys() == component.keys()
assert all(full[k]['success'] == component[k]['success'] for k in full)
counts = dict(both_correct=0, full_only_correct=0, component_only_correct=0, both_incorrect=0)
for k, row in full.items():
    f = row['predicted_success'] == row['success']
    c = component[k]['predicted_success'] == row['success']
    key = 'both_correct' if f and c else 'full_only_correct' if f else 'component_only_correct' if c else 'both_incorrect'
    counts[key] += 1
y = np.array([1 - r['success'] for r in full.values()])
p = np.array([1 - r['predicted_success'] for r in full.values()])
s = np.array([r['failure_score'] for r in full.values()])
precision, recall, _ = precision_recall_curve(y, s)
recomputed = dict(accuracy=accuracy_score(y, p), balanced_accuracy=balanced_accuracy_score(y, p), failure_auroc=roc_auc_score(y, s), failure_auprc_trapezoid=auc(recall, precision))
metrics = json.loads((root / names[0] / 'metrics.json').read_text())
error = max(abs(float(v) - metrics[k]) for k, v in recomputed.items())
assert error < 1e-12
manifest = Path('/root/autodl-tmp/models/ifailsense/asset_manifest_v1.json')
shutil.copy2(manifest, dest / names[0] / manifest.name)
audit = dict(samples=203, exact_source_rows_and_labels_match=True, paired_correctness=counts, recomputed_metrics=recomputed, maximum_metric_difference=error, accuracy_difference_percentage_points=100*(counts['full_only_correct']-counts['component_only_correct'])/203, scope='Paired descriptive component comparison; no claim of untouched OOD or full paper reproduction')
(dest / 'ifailsense_paired_audit.json').write_text(json.dumps(audit, indent=2) + '\n')
print(json.dumps(audit, indent=2))
