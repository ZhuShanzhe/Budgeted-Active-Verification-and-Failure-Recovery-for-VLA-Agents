"""Diagnostic ablation of the released VLM component, NOT full I-FailSense.

Uses the author next-token decoding that supplies the VLM vote. Unsupported
outputs remain abstentions and count as incorrect in all-sample accuracy.
"""
import argparse
import json
from pathlib import Path
import subprocess
import time
import torch
from datasets import load_dataset
from eval_ifailsense_fixed import FailSense, process_input, label, digest, UPSTREAM


def main(args):
    out = Path(args.output)
    if out.exists():
        raise FileExistsError(out)
    assets = json.loads(Path('/root/autodl-tmp/models/ifailsense/asset_manifest_v1.json').read_text())
    assert all('snapshot' in x for x in assets)
    by_repo = {x['repo']: x for x in assets}
    data = by_repo['ACIDE/AHA-Calvin-1p']
    paths = sorted(Path(data['snapshot']).glob('data/*validation*.parquet'))
    dataset = load_dataset('parquet', data_files={'validation':[str(x) for x in paths]}, split='validation')
    dataset = dataset.add_column('source_row', list(range(len(dataset))))
    dataset = dataset.train_test_split(test_size=.1, seed=42)['test']
    dataset = dataset.rename_column('image','images').rename_column('success','label')
    out.mkdir(parents=True)
    (out/'config.json').write_text(json.dumps(dict(assets=assets, batch_size=4, precision='float32', source_commit=subprocess.check_output(['git','-C',str(UPSTREAM),'rev-parse','HEAD'],text=True).strip(), script_sha256=digest(__file__),
        scope='Author VLM next-token vote only. No FS block predictions. Unsupported outputs are explicit abstentions.'),indent=2))
    torch.manual_seed(42)
    model = FailSense(by_repo['ACIDE/FailSense-Calvin-1p-3b']['snapshot'], device='cuda')
    model.eval()
    records=[]
    start=time.perf_counter()
    for offset in range(0,len(dataset),4):
        batch=dataset[offset:offset+4]
        prompts=[process_input(img,task) for img,task in zip(batch['images'],batch['task'])]
        with torch.inference_mode():
            decoded, features=model.extract_features(batch['images'],prompts,voting=True)
        del features
        for i,text in enumerate(decoded):
            value=text.strip().lower()
            prediction=1 if value in ['success','1','pass'] else 0 if value in ['fail','0','failure'] else None
            row=dict(index=offset+i,source_row=int(batch['source_row'][i]),success=label(batch['label'][i]),predicted_success=prediction,decoded=text)
            records.append(row)
            with (out/'predictions.jsonl').open('a') as stream:
                stream.write(json.dumps(row)+'\n')
        print(json.dumps(dict(evaluated=len(records),total=len(dataset))),flush=True)
    assert len(records)==len(dataset)
    classified=[r for r in records if r['predicted_success'] is not None]
    per_class={str(cls):dict(samples=sum(r['success']==cls for r in records),correct=sum(r['success']==cls and r['predicted_success']==cls for r in records)) for cls in [0,1]}
    metrics=dict(samples=len(records),abstentions=len(records)-len(classified),coverage=len(classified)/len(records),
        accuracy_abstentions_incorrect=sum(r['success']==r['predicted_success'] for r in records)/len(records),
        balanced_accuracy_abstentions_incorrect=sum(x['correct']/x['samples'] for x in per_class.values())/2,
        per_class=per_class,wall_seconds=time.perf_counter()-start,peak_allocated_bytes=torch.cuda.max_memory_allocated(),
        scope='VLM component diagnostic, not full I-FailSense or calibrated failure risk. Randomly initialized FS heads in author constructor are never called.')
    (out/'metrics.json').write_text(json.dumps(metrics,indent=2))
    (out/'completed.json').write_text(json.dumps(dict(status='complete',samples=len(records),skipped=0),indent=2))
    model.cleanup()
    print(json.dumps(metrics,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--output',required=True)
    main(parser.parse_args())
