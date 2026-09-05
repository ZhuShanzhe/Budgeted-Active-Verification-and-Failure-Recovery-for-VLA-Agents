#!/usr/bin/env bash
set -euo pipefail
cd /root/autodl-tmp/projects/Budgeted-Active-Verification-and-Failure-Recovery-for-VLA-Agents
export OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 WANDB_MODE=disabled
if ! test -f /root/autodl-tmp/datasets/safe-rollouts/droid-extracted-v1/raw_metadata_audit.json; then
  /root/autodl-tmp/conda-envs/vla-safe/bin/python scripts/audit_droid_metadata.py \
    --root /root/autodl-tmp/datasets/safe-rollouts/droid-extracted-v1 \
    --output /root/autodl-tmp/datasets/safe-rollouts/droid-extracted-v1/raw_metadata_audit.json
fi
for model in lstm indep; do
  for seed in 0 1 2; do
    run="/root/autodl-tmp/experiments/baselines-20260905/safe-droid-v1-${model}-seed${seed}"
    if test -f "${run}/completed.json"; then continue; fi
    if test -e "$run"; then
      echo "Unfinished or conflicting output; explicit review required: $run" >&2
      exit 1
    fi
    reg=0.001
    if test "$model" = indep; then reg=0.01; fi
    SAFE_AUDIT_DIR="$run" /root/autodl-tmp/conda-envs/vla-safe/bin/python scripts/safe_logged_train.py \
      dataset=pizero_fast_droid_0510 \
      dataset.data_path_prefix=/root/autodl-tmp/datasets/safe-rollouts/droid-extracted-v1/ \
      dataset.feat_name=pre_logits dataset.token_idx_rel=mean dataset.load_to_cuda=False \
      dataset.normalize_hidden_states=False \
      model="$model" model.batch_size=64 model.lr=1e-4 model.lambda_reg="$reg" model.n_epochs=1000 \
      train.seed="$seed" train.roc_every=250 train.eval_save_ckpt=True \
      train.eval_save_logs=True train.logs_save_path="$run" \
      > "/root/autodl-tmp/logs/safe_droid_v1_${model}_seed${seed}.log" 2>&1
  done
done
/root/autodl-tmp/conda-envs/vla-safe/bin/python scripts/eval_saved_safe.py \
  --run-prefix /root/autodl-tmp/experiments/baselines-20260905/safe-droid-v1 \
  --exclude-label-audit /root/autodl-tmp/datasets/safe-rollouts/droid-extracted-v1/raw_metadata_audit.json \
  > /root/autodl-tmp/logs/safe_droid_independent_evaluation_v1.log 2>&1
/root/autodl-tmp/conda-envs/vla-safe/bin/python scripts/export_safe_droid.py
