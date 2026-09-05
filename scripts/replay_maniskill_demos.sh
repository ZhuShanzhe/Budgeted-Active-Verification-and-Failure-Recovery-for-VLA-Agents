#!/usr/bin/env bash
set -euo pipefail
export MS_ASSET_DIR=/root/autodl-tmp/datasets/maniskill3/assets
export OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
for task in PickCube-v1 StackCube-v1 PegInsertionSide-v1; do
  source_dir="/root/autodl-tmp/datasets/maniskill3/demos/$task/motionplanning"
  target="/root/autodl-tmp/experiments/baselines-20260905/maniskill-replay/$task"
  mkdir -p "$target"
  for ext in h5 json; do
    if ! test -e "$target/trajectory.$ext"; then
      ln -s "$source_dir/trajectory.$ext" "$target/trajectory.$ext"
    fi
  done
  /root/autodl-tmp/conda-envs/maniskill3/bin/python -m mani_skill.trajectory.replay_trajectory \
    --traj-path "$target/trajectory.h5" --obs-mode rgb+depth --count 3 --num-envs 1 \
    --save-traj --save-video --allow-failure --max-retry 0 \
    > "/root/autodl-tmp/logs/maniskill_replay_${task}.log" 2>&1
done
