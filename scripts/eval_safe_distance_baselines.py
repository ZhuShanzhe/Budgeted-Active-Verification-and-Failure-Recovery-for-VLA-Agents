"""Official SAFE distance baselines, frozen k=5, exact prior episode splits.

No model or evaluation formula changes. Train-only banks are saved separately
because upstream EmbedModel does not register them in its state_dict.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

os.environ['WANDB_MODE'] = 'disabled'
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'third_party/SAFE'))
import numpy as np
import torch
import wandb
from omegaconf import OmegaConf
from torch.utils.data import DataLoader
from failure_prob.conf import EmbedModelConfig
from failure_prob.data import load_rollouts, split_rollouts
from failure_prob.data.utils import RolloutDataset
from failure_prob.model.embed import EmbedModel
from failure_prob.utils.random import seed_everything
from failure_prob.utils.routines import model_forward_dataloader
from failure_prob.utils.metrics import eval_scores_roc_prc, eval_split_conformal
from failure_prob.utils.constants import EVAL_TIME_QUANTILES


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(8*1024*1024), b''): h.update(chunk)
    return h.hexdigest()


def save_results(path, result):
    scalars = {}
    for key, value in result.items():
        if isinstance(value, (int, float, np.number)):
            scalars[key] = float(value)
        elif isinstance(value, wandb.Table):
            (path/(key.replace('/', '__')+'.json')).write_text(json.dumps(dict(columns=value.columns, data=value.data), default=str))
    return scalars


def main(args):
    base = Path(args.output)
    base.mkdir(parents=True, exist_ok=True)
    wandb.init(mode='disabled')
    for domain, prefix in [('widowx','safe-v2'), ('droid','safe-droid-v1')]:
        for seed in range(3):
            reference = Path('/root/autodl-tmp/experiments/baselines-20260905') / f'{prefix}-lstm-seed{seed}'
            cfg = OmegaConf.load(reference/'config.yaml')
            seed_everything(0); pool = load_rollouts(cfg)
            seed_everything(seed); splits = split_rollouts(cfg, pool)
            saved_splits = json.loads((reference/'splits.json').read_text())
            if {k:[r.mp4_path for r in v] for k,v in splits.items()} != {k:[r['path'] for r in v] for k,v in saved_splits.items()}:
                raise ValueError('Prior split mismatch')
            if {r.task_id for r in splits['train']} & {r.task_id for r in splits['val_unseen']}:
                raise ValueError('Task leakage')
            paths = [{r.mp4_path for r in rows} for rows in splits.values()]
            if any(paths[i]&paths[j] for i in range(len(paths)) for j in range(i)):
                raise ValueError('Episode leakage')
            cfg.model = OmegaConf.structured(EmbedModelConfig())
            cfg.model.topk = 5; cfg.model.cumsum = False; cfg.model.use_success_only = False
            cfg.model.batch_size = 8
            datasets = {k:RolloutDataset(cfg,v) for k,v in splits.items()}
            loaders = {k:DataLoader(d,batch_size=8,shuffle=False) for k,d in datasets.items()}
            for distance in ['cosine','euclid']:
                out = base/f'{domain}-{distance}-seed{seed}'
                if (out/'completed.json').exists(): continue
                if out.exists(): raise FileExistsError('Preserve partial run: '+str(out))
                out.mkdir(); cfg.model.distance = distance
                OmegaConf.save(cfg,out/'config.yaml')
                (out/'splits.json').write_text(json.dumps(saved_splits,indent=2))
                started=time.perf_counter()
                print(json.dumps(dict(starting=out.name)),flush=True)
                model=EmbedModel(cfg,pool[0].hidden_states.shape[-1]).to('cuda')
                model.train_epoch(None,loaders['train']); model.eval()
                bank=dict(feats_succ=model.feats_succ.cpu(),feats_fail=model.feats_fail.cpu())
                torch.save(bank,out/'train_feature_bank.pt')
                del bank
                score_arrays={}; curves={}
                with torch.no_grad():
                    for split,loader in loaders.items():
                        score,mask,label=model_forward_dataloader(model,loader)
                        if not torch.isfinite(score[mask.bool()]).all(): raise ValueError('Invalid score')
                        score_arrays[split]=(score.cpu(),mask.cpu(),label.cpu())
                        lengths=mask.sum(-1).int().cpu().tolist()
                        curves[split]=[score[i,:n].cpu().numpy() for i,n in enumerate(lengths)]
                        np.savez_compressed(out/f'scores_{split}.npz',scores=score.cpu().numpy(),valid_masks=mask.cpu().numpy(),success_labels=label.cpu().numpy())
                del model; torch.cuda.empty_cache()
                reloaded=EmbedModel(cfg,pool[0].hidden_states.shape[-1]).to('cuda')
                bank=torch.load(out/'train_feature_bank.pt',map_location='cuda',weights_only=True)
                reloaded.feats_succ=bank['feats_succ']; reloaded.feats_fail=bank['feats_fail']; reloaded.trained=True; reloaded.eval()
                difference=0.0
                with torch.no_grad():
                    for split in ['val_seen','val_unseen']:
                        check,mask,label=model_forward_dataloader(reloaded,loaders[split])
                        previous,oldmask,oldlabel=score_arrays[split]
                        if not torch.equal(mask.cpu(),oldmask) or not torch.equal(label.cpu(),oldlabel): raise ValueError('Reload ordering mismatch')
                        difference=max(difference,float((check.cpu()-previous).abs().max()))
                if difference>1e-6: raise ValueError('Reload score mismatch')
                metrics=eval_scores_roc_prc(splits,curves,'model',EVAL_TIME_QUANTILES[cfg.dataset.name],False,False)
                scalars=save_results(out,metrics)
                cp=eval_split_conformal(splits,curves,'model',calib_split_names=['val_seen'],test_split_names=['val_unseen'])
                (out/'conformal.json').write_text(json.dumps(cp,indent=2,default=str))
                if domain=='droid':
                    audit=json.loads(Path('/root/autodl-tmp/datasets/safe-rollouts/droid-extracted-v1/raw_metadata_audit.json').read_text())
                    flagged={r['path'].replace('meta.pkl','external_left.mp4') for r in audit['label_issues']}
                    indices={k:[i for i,r in enumerate(rows) if r.mp4_path not in flagged] for k,rows in splits.items()}
                    clean={k:[splits[k][i] for i in ii] for k,ii in indices.items()}
                    clean_scores={k:[curves[k][i] for i in ii] for k,ii in indices.items()}
                    sensitive=eval_scores_roc_prc(clean,clean_scores,'model',EVAL_TIME_QUANTILES[cfg.dataset.name],False,False)
                    (out/'sensitivity.json').write_text(json.dumps({k:float(v) for k,v in sensitive.items() if isinstance(v,(int,float,np.number))},indent=2))
                (out/'final_metrics.json').write_text(json.dumps(scalars,indent=2))
                completed=dict(status='complete',domain=domain,distance=distance,seed=seed,bank_sha256=sha(out/'train_feature_bank.pt'),
                               bank_source='train only; all valid steps from successful and failed training rollouts',
                               source_split_sha256=sha(reference/'splits.json'),script_sha256=sha(__file__),
                               reload_max_abs_error=difference,wall_seconds=time.perf_counter()-started,
                               scope='Official SAFE EmbedModel; k=5, both classes, no cumsum; fixed configuration not full paper grid')
                (out/'completed.json').write_text(json.dumps(completed,indent=2))
                print(json.dumps(dict(completed=out.name,early_auroc=scalars['falert_early_roc_auc/model_val_unseen'],reload_error=difference)),flush=True)
                del reloaded,bank,score_arrays,curves; torch.cuda.empty_cache()
            del pool,splits,datasets,loaders


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--output',required=True); main(p.parse_args())
