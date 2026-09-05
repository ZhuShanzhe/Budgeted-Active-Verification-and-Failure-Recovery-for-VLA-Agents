"""Fingerprint used weights and check exported SAFE prediction arrays."""
import hashlib
import json
from pathlib import Path

import numpy as np

root = Path(__file__).resolve().parents[1]
exp = Path('/root/autodl-tmp/experiments/baselines-20260905')
files = []
for name in ['openvla-7b-oft-libero-spatial', 'avavla-libero-4in1']:
    folder = Path('/root/autodl-tmp/checkpoints') / name
    files.extend(p for p in folder.iterdir() if p.suffix in ['.safetensors', '.pt', '.json', '.py', '.model'])
arrays = []
for seed in range(3):
    model_splits = []
    for model in ['lstm', 'indep']:
        run = exp / f'safe-v2-{model}-seed{seed}'
        files.append(run / 'model_final.ckpt')
        splits = json.loads((run / 'splits.json').read_text())
        model_splits.append(splits)
        for split, rows in splits.items():
            path = run / f'scores_{split}.npz'
            with np.load(path, allow_pickle=False) as saved:
                scores = saved['scores']
                masks = saved['valid_masks'].astype(bool)
                labels = saved['success_labels'].reshape(-1)
                assert scores.shape == masks.shape
                assert scores.shape[0] == len(rows) == len(labels)
                assert np.isfinite(scores[masks]).all()
                assert (masks.sum(axis=1) > 0).all()
                assert np.array_equal(labels, [int(r['success']) for r in rows])
                arrays.append(dict(run=run.name, split=split, episodes=len(rows),
                                   valid_scores=int(masks.sum()), finite_and_labels_passed=True))
    assert model_splits[0] == model_splits[1], f'MLP/LSTM split mismatch, seed {seed}'
weights = []
for path in sorted(files):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        while block := source.read(8 * 1024 * 1024):
            digest.update(block)
    weights.append(dict(path=str(path), bytes=path.stat().st_size, sha256=digest.hexdigest()))
    print('FINGERPRINTED', path.name, flush=True)
out = root / 'docs/reproduction/results/20260905/artifact_audit.json'
out.write_text(json.dumps(dict(
    weights_and_configs=weights, safe_arrays=arrays, same_seed_mlp_lstm_splits_equal=True,
    caveat='SHA-256 fingerprints the exact local artifacts; it does not by itself establish publisher authenticity.'), indent=2))
print('ARTIFACT_AUDIT_COMPLETE', flush=True)
