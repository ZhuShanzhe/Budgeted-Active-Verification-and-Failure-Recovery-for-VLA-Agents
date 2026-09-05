"""Verify paired policy runs and export descriptive results, not causal claims."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
exp = Path('/root/autodl-tmp/experiments/baselines-20260905')
results = {}
for benchmark, count in [('clean', 50), ('plus', 70)]:
    runs = {}
    selections = []
    configs = []
    for policy in ['oft', 'ava']:
        run = exp / f'{policy}-{benchmark}-spatial-{count}'
        summary = json.loads((run / 'summary.json').read_text())
        rows = [json.loads(line) for line in (run / 'episodes.jsonl').read_text().splitlines()]
        keyed = {(row['task_id'], row['initial_state_index']): row for row in rows}
        assert len(rows) == len(keyed) == summary['episodes'] == count
        assert sum(row['success'] for row in rows) == summary['successes']
        assert all(row['infrastructure_error'] is None for row in rows)
        assert all(row['policy_queries'] > 0 and row['steps'] > 0 for row in rows)
        runs[policy] = keyed
        selections.append(json.loads((run / 'task_selection.json').read_text()))
        configs.append(json.loads((run / 'config.json').read_text()))
    assert selections[0] == selections[1]
    assert configs[0]['libero_commit'] == configs[1]['libero_commit']
    for field in ['seed', 'num_trials_per_task', 'env_img_res', 'num_open_loop_steps',
                  'num_images_in_input', 'use_proprio', 'center_crop']:
        assert configs[0]['config'][field] == configs[1]['config'][field], field
    assert runs['oft'].keys() == runs['ava'].keys()
    paired = []
    for key, oft in runs['oft'].items():
        ava = runs['ava'][key]
        for field in ['task', 'category', 'seed']:
            assert oft[field] == ava[field], (key, field)
        paired.append(dict(task_id=key[0], initial_state_index=key[1],
                           category=oft['category'], task_prompt=oft['task'],
                           oft_success=oft['success'], ava_success=ava['success']))
    table = {category: dict(
        episodes=sum(r['category'] == category for r in paired),
        oft_successes=sum(r['category'] == category and r['oft_success'] for r in paired),
        ava_successes=sum(r['category'] == category and r['ava_success'] for r in paired))
        for category in sorted({r['category'] for r in paired})}
    results[benchmark] = dict(
        episodes=count, checks='complete; no infrastructure errors; identical selected tasks, prompts and state indices',
        selection_sha256=hashlib.sha256(json.dumps(selections[0], sort_keys=True).encode()).hexdigest(),
        per_category=table,
        both_success=sum(r['oft_success'] and r['ava_success'] for r in paired),
        oft_only_success=sum(r['oft_success'] and not r['ava_success'] for r in paired),
        ava_only_success=sum(not r['oft_success'] and r['ava_success'] for r in paired),
        both_failure=sum(not r['oft_success'] and not r['ava_success'] for r in paired),
        paired_episodes=paired,
        caveat='Different checkpoint training scopes; finite clustered samples. Plus uses upstream prompts with perturbation suffixes; diagnostic only.')
out = root / 'docs/reproduction/results/20260905/paired_policy_audit.json'
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(results, indent=2))
print(json.dumps({k: {a:b for a,b in v.items() if a != 'paired_episodes'} for k,v in results.items()}, indent=2))
