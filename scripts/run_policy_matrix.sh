#!/usr/bin/env bash
set -eo pipefail
cd /root/autodl-tmp/projects/Budgeted-Active-Verification-and-Failure-Recovery-for-VLA-Agents
source /root/miniconda3/etc/profile.d/conda.sh
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4
for benchmark in clean plus; do
  for policy in oft ava; do
    if test "$policy" = oft; then profile=openvla-oft; else profile=ava-vla; fi
    conda activate "/root/autodl-tmp/conda-envs/$profile"
    trials=5
    count=50
    if test "$benchmark" = plus; then trials=1; count=70; fi
    run="/root/autodl-tmp/experiments/baselines-20260905/${policy}-${benchmark}-spatial-${count}"
    if test -f "$run/summary.json"; then continue; fi
    python scripts/eval_policy_audit.py --policy "$policy" --benchmark "$benchmark" \
      --trials "$trials" --output "$run" \
      > "/root/autodl-tmp/logs/${policy}_${benchmark}_spatial_${count}.log" 2>&1
  done
done
