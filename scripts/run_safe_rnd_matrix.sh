#!/usr/bin/env bash
set -euo pipefail
cd /root/autodl-tmp/projects/Budgeted-Active-Verification-and-Failure-Recovery-for-VLA-Agents
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 WANDB_MODE=disabled
for domain in widowx droid; do
  for seed in 0 1 2; do
    run="/root/autodl-tmp/experiments/baselines-20260905/safe-rnd-v1/${domain}-seed${seed}"
    if test -f "$run/completed.json"; then continue; fi
    if test -e "$run"; then echo "Partial run requires explicit review: $run" >&2; exit 1; fi
    /root/autodl-tmp/conda-envs/vla-safe/bin/python scripts/train_safe_rnd_baseline.py \
      --domain "$domain" --seed "$seed" --epochs 200 --batch-size 32 --output "$run" \
      > "/root/autodl-tmp/logs/safe_rnd_v1_${domain}_seed${seed}.log" 2>&1
    echo "Completed $domain seed $seed"
  done
done
