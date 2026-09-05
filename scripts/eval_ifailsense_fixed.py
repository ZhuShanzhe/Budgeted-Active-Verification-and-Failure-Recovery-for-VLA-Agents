"""Fail-closed evaluation of one frozen official I-FailSense checkpoint.

Dataset: author CALVIN validation -> 10% test split, seed 42. No test selection
of checkpoint, input representation, threshold, batch size or precision.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np
import torch
from datasets import load_dataset
from sklearn.metrics import (accuracy_score, balanced_accuracy_score,
                             confusion_matrix, f1_score, precision_recall_curve,
                             roc_auc_score, auc)

UPSTREAM = Path('/root/autodl-tmp/projects/baseline-audit/I-FailSense')
sys.path.insert(0, str(UPSTREAM / 'src'))
from model import FailSense, process_input


def digest(path):
    hasher = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
            hasher.update(block)
    return hasher.hexdigest()


def label(value):
    if value in (0, '0', 'fail', 'failure'):
        return 0
    if value in (1, '1', 'success'):
        return 1
    raise ValueError('Unexpected label value; no automatic relabeling')


def main(args):
    out = Path(args.output)
    if out.exists():
        raise FileExistsError('Preserve earlier results: ' + str(out))
    assets = json.loads(Path(args.manifest).read_text())
    by_repo = {item['repo']: item for item in assets}
    adapter = by_repo['ACIDE/FailSense-Calvin-1p-3b']
    data = by_repo['ACIDE/AHA-Calvin-1p']
    assert all('snapshot' in row for row in assets), 'Incomplete downloads'
    files = sorted(Path(data['snapshot']).glob('data/*validation*.parquet'))
    assert len(files) == 1, files
    out.mkdir(parents=True)
    # Local pinned parquet has the same source row order as the author split.
    validation = load_dataset('parquet', data_files={'validation': [str(x) for x in files]}, split='validation')
    validation = validation.add_column('source_row', list(range(len(validation))))
    dataset = validation.train_test_split(test_size=0.1, seed=42)['test']
    dataset = dataset.rename_column('image', 'images').rename_column('success', 'label')
    manifest = [dict(source_row=int(x['source_row']), task=x['task'], success=label(x['label'])) for x in dataset]
    (out / 'evaluation_manifest.json').write_text(json.dumps(manifest, indent=2))
    cfg = dict(checkpoint=str(Path(args.checkpoint).resolve()), checkpoint_sha256=digest(args.checkpoint),
               assets=assets, source_commit=subprocess.check_output(['git', '-C', str(UPSTREAM), 'rev-parse', 'HEAD'], text=True).strip(),
               batch_size=4, precision='float32 (upstream default)', voting=True,
               split='CALVIN validation.train_test_split(test_size=0.1,seed=42)[test]',
               num_samples=len(dataset), checkpoint_selection='Single checkpoint specified before inference; no test-based selection',
               script_sha256=digest(__file__))
    (out / 'config.json').write_text(json.dumps(cfg, indent=2))
    # Force locally downloaded base; upstream model ID resolves through its cache.
    os.environ['HF_HUB_OFFLINE'] = '1'
    torch.manual_seed(42)
    model = FailSense(adapter['snapshot'], device='cuda')
    # Load only the tensor/state dictionary schema reviewed in the author code.
    state = torch.load(args.checkpoint, map_location='cuda', weights_only=True)
    assert state['num_classifiers'] == model.num_classifiers
    for i in range(model.num_classifiers):
        model.classifiers[i].load_state_dict(state[f'classifier_{i}'], strict=True)
        model.att_poolings[i].load_state_dict(state[f'attention_pooling_{i}'], strict=True)
    del state
    model.eval()
    records = []
    start = time.perf_counter()
    for offset in range(0, len(dataset), 4):
        batch = dataset[offset:offset + 4]
        images = batch['images']
        prompts = [process_input(img, task) for img, task in zip(images, batch['task'])]
        torch.cuda.synchronize()
        before = time.perf_counter()
        with torch.inference_mode():
            predictions, votes = model.predict(images, prompts, voting=True)
        torch.cuda.synchronize()
        elapsed = time.perf_counter() - before
        predictions = predictions.detach().cpu().tolist()
        votes = votes.detach().cpu().tolist()
        assert len(predictions) == len(images) == len(votes)
        for i, (prediction, vote) in enumerate(zip(predictions, votes)):
            assert np.isfinite(vote) and 0 <= vote <= 1
            assert prediction in (0., 1.)
            record = dict(index=offset + i, source_row=int(batch['source_row'][i]),
                          success=label(batch['label'][i]), predicted_success=int(prediction),
                          success_vote_fraction=float(vote), failure_score=1 - float(vote))
            records.append(record)
            with (out / 'predictions.jsonl').open('a') as stream:
                stream.write(json.dumps(record) + '\n')
        print(json.dumps(dict(evaluated=len(records), total=len(dataset), batch_seconds=elapsed)), flush=True)
    assert len(records) == len(dataset)
    y = np.asarray([1 - r['success'] for r in records])
    pred = np.asarray([1 - r['predicted_success'] for r in records])
    scores = np.asarray([r['failure_score'] for r in records])
    assert set(y) == {0, 1}, 'Both classes required for AUROC'
    precision, recall, _ = precision_recall_curve(y, scores)
    metrics = dict(samples=len(records), success_count=int((y == 0).sum()), failure_count=int(y.sum()),
                   accuracy=float(accuracy_score(y, pred)), balanced_accuracy=float(balanced_accuracy_score(y, pred)),
                   failure_f1=float(f1_score(y, pred, zero_division=0)), failure_auroc=float(roc_auc_score(y, scores)),
                   failure_auprc_trapezoid=float(auc(recall, precision)),
                   confusion_true_rows_pred_columns_success_failure=confusion_matrix(y, pred, labels=[0, 1]).tolist(),
                   scope='One released CALVIN checkpoint, author 10% validation-derived split; not full paper reproduction or a proven untouched OOD benchmark',
                   scores='Vote fractions, not calibrated probabilities',
                   inference_wall_seconds=time.perf_counter() - start,
                   peak_allocated_bytes=torch.cuda.max_memory_allocated())
    (out / 'metrics.json').write_text(json.dumps(metrics, indent=2))
    model.cleanup()
    (out / 'completed.json').write_text(json.dumps(dict(status='complete', samples=len(records), skipped=0), indent=2))
    print(json.dumps(metrics, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', required=True)
    parser.add_argument('--manifest', default='/root/autodl-tmp/models/ifailsense/asset_manifest_v1.json')
    parser.add_argument('--output', required=True)
    main(parser.parse_args())
