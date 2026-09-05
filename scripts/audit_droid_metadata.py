"""Audit original metadata/video links, without inventing missing camera recordings."""
import argparse
import collections
import json
import math
import pickle
import re
from pathlib import Path


def audit(root):
    rows=[]; issues=[]; label_issues=[]
    for path in sorted(Path(root).glob('rollouts_all/*/*/env_records/*--meta.pkl')):
        meta=pickle.load(path.open('rb'))
        match=re.fullmatch(r'task(\d+)--ep(\d+)--succ([01])--meta.pkl',path.name)
        if not match: raise ValueError('Invalid metadata filename')
        task,episode,label=map(int,match.groups())
        raw_label=float(meta['episode_success'])
        if not math.isfinite(raw_label) or not 0<=raw_label<=1 or int(meta['episode_idx'])!=episode:
            raise ValueError('Invalid metadata label or episode identity: '+str(path))
        if raw_label not in [0,1] or int(raw_label)!=label:
            label_issues.append(dict(path=str(path),filename_label=label,metadata_label=raw_label,
                official_integer_label=int(raw_label),nonbinary_metadata=raw_label not in [0,1],
                policy='Preserve archive; official reproduction uses int(metadata), exclude from reliable new-model supervision pending review.'))
        videos={camera:path.with_name(path.name.replace('meta.pkl',camera+'.mp4')).is_file() for camera in ['external_left','wrist']}
        row=dict(path=str(path),task_id=task,episode_id=episode,task_description=meta['task_description'],success=bool(int(raw_label)),
            filename_label=label,metadata_label=raw_label,replan_steps=meta['replan_steps'],end_step=meta.get('end_step'),videos=videos)
        rows.append(row)
        if not all(videos.values()): issues.append(dict(path=str(path),missing=[k for k,v in videos.items() if not v]))
    return dict(raw_episodes=len(rows),successes=sum(r['success'] for r in rows),failures=sum(not r['success'] for r in rows),
        task_descriptions=dict(collections.Counter(r['task_description'] for r in rows)),video_link_issues=issues,label_issues=label_issues,
        nonbinary_labels=sum(r['nonbinary_metadata'] for r in label_issues),records=rows,
        label_policy='Official loader int(metadata episode_success), not filename; this does not establish which anomalous labels are factually correct.',
        scope='Raw archive audit before official task/length/balance filtering; videos have not been exhaustively decoded.')


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--root',required=True); p.add_argument('--output',required=True); a=p.parse_args()
    target=Path(a.output)
    if target.exists(): raise FileExistsError(target)
    result=audit(a.root); target.write_text(json.dumps(result,indent=2)); print(json.dumps({k:v for k,v in result.items() if k!='records'},indent=2))
