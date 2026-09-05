"""Official RND detector in SAFE, with exact existing splits and fail-fast logs."""
import argparse
import gc
import json
import math
import os
from pathlib import Path
import sys
import time
os.environ['WANDB_MODE']='disabled'
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'third_party/SAFE'))
import numpy as np
import torch
import wandb
from omegaconf import OmegaConf
from torch.utils.data import DataLoader
from failure_prob.conf import RNDModelConfig
from failure_prob.data import load_rollouts,split_rollouts
from failure_prob.data.utils import RolloutDataset
from failure_prob.model import get_model
from failure_prob.utils.random import seed_everything
from failure_prob.utils.routines import model_forward_dataloader
from failure_prob.utils.metrics import eval_scores_roc_prc,eval_split_conformal
from failure_prob.utils.constants import EVAL_TIME_QUANTILES


class MergedTailBatches:
    """Preserve every training trajectory; merge tails smaller than half a batch.

    Upstream RND takes separate class means: a tiny one-class tail gives NaN.
    This is an explicit batching adaptation, not silently dropping that batch.
    """
    def __init__(self, size, batch_size): self.size=size; self.batch_size=batch_size
    def __iter__(self):
        order=torch.randperm(self.size).tolist()
        batches=[order[i:i+self.batch_size] for i in range(0,self.size,self.batch_size)]
        if len(batches)>1 and len(batches[-1])<self.batch_size//2:
            batches[-2].extend(batches.pop())
        return iter(batches)
    def __len__(self):
        full,tail=divmod(self.size,self.batch_size)
        return full+int(tail>0)-int(full>0 and 0<tail<self.batch_size//2)


def main(args):
    out=Path(args.output)
    if out.exists(): raise FileExistsError(out)
    out.mkdir(parents=True)
    prefix='safe-v2' if args.domain=='widowx' else 'safe-droid-v1'
    source=Path('/root/autodl-tmp/experiments/baselines-20260905')/f'{prefix}-lstm-seed{args.seed}'
    cfg=OmegaConf.load(source/'config.yaml')
    cfg.model=OmegaConf.structured(RNDModelConfig())
    cfg.model.batch_size=args.batch_size; cfg.model.n_epochs=args.epochs
    OmegaConf.save(cfg,out/'config.yaml')
    seed_everything(0); pool=load_rollouts(cfg)
    seed_everything(args.seed); splits=split_rollouts(cfg,pool)
    recorded=json.loads((source/'splits.json').read_text())
    if {k:[r.mp4_path for r in rows] for k,rows in splits.items()}!={k:[r['path'] for r in rows] for k,rows in recorded.items()}: raise ValueError('Split mismatch')
    (out/'splits.json').write_text(json.dumps(recorded,indent=2))
    datasets={k:RolloutDataset(cfg,v) for k,v in splits.items()}
    train_loader=DataLoader(datasets['train'],batch_sampler=MergedTailBatches(len(datasets['train']),args.batch_size))
    model=get_model(cfg,pool[0].hidden_states.shape[-1]); model.to('cuda')
    optimizer,scheduler=model.get_optimizer()
    wandb.init(mode='disabled')
    start=time.perf_counter()
    for epoch in range(args.epochs):
        before=time.perf_counter(); model.train()
        loss=model.train_epoch(optimizer,train_loader)
        if not math.isfinite(float(loss)): raise ValueError('Nonfinite official RND loss; no silent batch skipping')
        if scheduler: scheduler.step()
        row=dict(epoch=epoch+1,loss=float(loss),seconds=time.perf_counter()-before,max_memory_bytes=torch.cuda.max_memory_allocated())
        with (out/'training.jsonl').open('a') as stream: stream.write(json.dumps(row)+'\n')
        print(json.dumps(row),flush=True)
    if args.probe:
        (out/'probe_complete.json').write_text(json.dumps(dict(epochs=args.epochs,scope='Train-only resource probe, not a benchmark',wall_seconds=time.perf_counter()-start)))
        return
    torch.save(model.state_dict(),out/'model_final.ckpt')
    model.eval()
    probe_batch=next(iter(DataLoader(datasets['val_seen'],batch_size=1,shuffle=False)))
    probe_batch={k:v.to('cuda') if torch.is_tensor(v) else v for k,v in probe_batch.items()}
    with torch.no_grad(): reference=model(probe_batch).cpu()
    del model,optimizer,scheduler; gc.collect(); torch.cuda.empty_cache()
    model=get_model(cfg,pool[0].hidden_states.shape[-1]); model.to('cuda')
    model.load_state_dict(torch.load(out/'model_final.ckpt',map_location='cuda',weights_only=True)); model.eval()
    with torch.no_grad(): error=float((model(probe_batch).cpu()-reference).abs().max())
    if error>1e-6: raise ValueError('Checkpoint reload mismatch')
    curves={}
    with torch.no_grad():
        for split,data in datasets.items():
            score,mask,label=model_forward_dataloader(model,DataLoader(data,batch_size=args.batch_size,shuffle=False))
            if not torch.isfinite(score[mask.bool()]).all(): raise ValueError('Invalid predictions')
            lengths=mask.sum(-1).int().cpu().tolist()
            curves[split]=[score[i,:n].cpu().numpy() for i,n in enumerate(lengths)]
            np.savez_compressed(out/f'scores_{split}.npz',scores=score.cpu().numpy(),valid_masks=mask.cpu().numpy(),success_labels=label.cpu().numpy())
    metrics=eval_scores_roc_prc(splits,curves,'model',EVAL_TIME_QUANTILES[cfg.dataset.name],False,False)
    scalars={k:float(v) for k,v in metrics.items() if isinstance(v,(int,float,np.number))}
    (out/'final_metrics.json').write_text(json.dumps(scalars,indent=2))
    cp=eval_split_conformal(splits,curves,'model',calib_split_names=['val_seen'],test_split_names=['val_unseen'])
    (out/'conformal.json').write_text(json.dumps(cp,indent=2,default=str))
    (out/'completed.json').write_text(json.dumps(dict(status='complete',epochs=args.epochs,batch_size=args.batch_size,seed=args.seed,domain=args.domain,
        reload_probe_max_error=error,wall_seconds=time.perf_counter()-start,batching='Random permutation; merge tails smaller than half batch; no trajectories dropped',
        scope='Official SAFE RND network/loss; batch 32 with merged tails; fixed config and prior splits, no test-based tuning'),indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--domain',choices=['widowx','droid'],required=True)
    p.add_argument('--seed',type=int,choices=range(3),required=True); p.add_argument('--epochs',type=int,default=200)
    p.add_argument('--batch-size',type=int,default=32); p.add_argument('--probe',action='store_true')
    p.add_argument('--output',required=True); main(p.parse_args())
