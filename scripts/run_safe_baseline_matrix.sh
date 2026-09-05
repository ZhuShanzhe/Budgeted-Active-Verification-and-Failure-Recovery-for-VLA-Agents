#!/usr/bin/env bash
set -euo pipefail
cd /root/autodl-tmp/projects/Budgeted-Active-Verification-and-Failure-Recovery-for-VLA-Agents
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 WANDB_MODE=disabled
for model in lstm indep; do
  for seed in 0 1 2; do
    run="/root/autodl-tmp/experiments/baselines-20260905/safe-v2-${model}-seed${seed}"
    if test -f "${run}/completed.json"; then continue; fi
    if test -f "${run}/metrics.jsonl"; then
      echo "Refusing to mix a new run with unfinished output: ${run}" >&2
      exit 1
    fi
    reg=0.001
    if test "$model" = indep; then reg=0.01; fi
    SAFE_AUDIT_DIR="$run" /root/autodl-tmp/conda-envs/vla-safe/bin/python scripts/safe_logged_train.py \
      dataset=openvla_widowx \
      dataset.data_path_prefix=/root/autodl-tmp/datasets/safe-rollouts/widowx-extracted/ \
      dataset.token_idx_rel=mean dataset.load_to_cuda=False \
      model="$model" model.batch_size=64 model.lr=1e-4 model.lambda_reg="$reg" \
      train.seed="$seed" train.roc_every=250 train.eval_save_ckpt=True \
      train.eval_save_logs=True train.logs_save_path="$run" \
      > "/root/autodl-tmp/logs/safe_v2_${model}_seed${seed}.log" 2>&1
  done
done
