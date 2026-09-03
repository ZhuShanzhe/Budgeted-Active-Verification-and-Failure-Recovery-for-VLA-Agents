# Baseline reproduction protocol

## Selection rule

A method enters the numerical comparison only when it satisfies all of the following:

1. it measures a distinct capability required by the research question;
2. official code is public and a checkpoint or a feasible training path exists;
3. its output can be evaluated on the same task split and cost accounting protocol;
4. reproduction is possible on one RTX 5090 without pretending to repeat multi-node pretraining.

The comparison keeps policy quality, active observation, failure verification, recovery, and OOD evaluation separate. This prevents an unfair comparison between a policy and a detector, and prevents several prior systems from being presented as one new model.

## Baseline matrix

| Baseline | Capability isolated | Numerical use | Reproduction target | Current server status |
| --- | --- | --- | --- | --- |
| OpenVLA-OFT | fixed-observation VLA policy | primary policy control | released LIBERO checkpoint, identical seeds and episode budget | official 7B checkpoint loaded; real LIBERO observation produced a finite `8 x 7` action chunk on GPU |
| AVA-VLA | history-based active visual attention | strongest direct active-observation comparison | released `avavla-libero-4in1` checkpoint on original LIBERO and LIBERO-Plus | official 7B checkpoint loaded; real LIBERO observation produced a finite `8 x 7` action chunk on GPU |
| SAFE | zero-shot multitask failure detection | verification and calibration | detector trained/evaluated from fixed OpenVLA rollout split | package and Hydra training entrypoint passed; rollout extractor added |
| AHA / FailGen | natural-language failure reasoning and synthetic failure modes | data/method reference; numerical entry only after a checkpoint is trained | included REFLECT subset and FailGen failure taxonomy | source and evaluation data present; official AHA model checkpoint is not public |
| LIBERO-Plus | seven-axis cross-distribution evaluation | common OOD benchmark | one fixed manifest covering all perturbation axes | official assets installed; headless EGL environment creation and both camera renders passed |

## Why these are direct comparisons

### OpenVLA-OFT

OpenVLA-OFT supplies the unchanged policy backbone and establishes the success/latency floor when no adaptive evidence is acquired. The proposed method must improve risk-adjusted success under a matched observation budget, not merely outperform an older VLA architecture.

### AVA-VLA

AVA-VLA is the direct comparison for adaptive use of visual history. It changes which temporal visual evidence is emphasized, but does not solve the full budgeted decision problem over heterogeneous tools, verification, and recovery. The comparison isolates whether gains come from active evidence routing rather than a stronger policy implementation.

### SAFE

SAFE is the direct verification baseline. It predicts failure from VLA features and provides calibration machinery, but does not decide which additional evidence to buy or which recovery action to execute. All detector comparisons use the same saved trajectories and split by task, not randomly by frame.

### AHA / FailGen

AHA contributes a failure taxonomy and failure-reasoning evaluation. Its released repository does not contain a downloadable final AHA checkpoint, and its reported full fine-tuning used eight A100 80GB GPUs. It is therefore not reported as a reproduced model until a checkpoint is trained or officially released. FailGen remains useful for constructing controlled failure categories.

### LIBERO-Plus

LIBERO-Plus provides camera, robot-state, language, lighting, texture, noise, and object-layout shifts. It is the primary OOD test bed. Original LIBERO remains the in-distribution reference; LIBERO-Plus measures cross-distribution robustness rather than replacing the clean evaluation.

## Evaluation protocol

### Splits

- Training and threshold selection never share trajectories with the final test set.
- Failure-detector splits are grouped by task and episode, never by individual frame.
- OOD results are reported separately for each perturbation axis and severity.
- A clean original-LIBERO score accompanies every OOD score to reveal robustness/quality tradeoffs.

### Budget

Every episode records:

- number and type of observations;
- image resolution and temporal window;
- calls to critics, depth, segmentation, retrieval, or other tools;
- wall-clock latency and GPU seconds;
- action replans and recovery attempts.

The main result is a success-cost Pareto frontier. Fixed-budget comparisons use identical maximum cost, and adaptive-budget comparisons report the full frontier rather than a single favorable operating point.

### Verification

Report AUROC, AUPRC, expected calibration error, Brier score, and risk-coverage curves. The action trigger is chosen on the validation split and frozen before testing.

### Task performance

Report task success, failure-recovery success, excess interventions, mean evidence cost, p95 latency, and success per unit cost. Confidence intervals are computed over episodes with fixed seeds shared across methods.

## Compute policy for one RTX 5090

- Reproduce released 7B checkpoints by inference and benchmark evaluation.
- Fine-tune lightweight heads, adapters, routers, critics, and calibration layers.
- Do not attempt to repeat full 7B pretraining or AHA's reported eight-A100 full fine-tuning.
- Cache VLA features and observations so detector/router ablations do not rerun the policy.
- Run a small deterministic smoke suite before any full benchmark.

## Additional papers and systems

- ActiveVLA is a close paper-level comparison for viewpoint selection and 3D zoom. Its official repository currently lists training, checkpoint, and evaluation release as pending, so it is not an executable baseline yet.
- LIBERO-Para is a complementary language-shift benchmark. It can be added after the seven LIBERO-Plus axes are stable, without changing the core method.
- LIBERO-Pro can serve as a secondary memorization/generalization audit after the primary comparison is complete.

These additions expand evaluation coverage; they do not replace the five core components above.

## Verified smoke-test evidence

- Hardware path: RTX 5090, CUDA 12.8 PyTorch build, `bfloat16` model inference.
- LIBERO path: a real `libero_spatial` task reset and rendered agent-view and wrist-view RGB observations through EGL.
- OpenVLA-OFT path: the released `moojink/openvla-7b-oft-finetuned-libero-spatial` checkpoint loaded with 7.54B parameters and generated a finite eight-action chunk from the real observation.
- AVA-VLA path: the released `LiAuto-DSR/avavla-libero-4in1` checkpoint loaded with 7.54B parameters and generated a finite eight-action chunk from the real observation.
- SAFE path: package import and Hydra training entrypoint completed; numerical detector results remain gated on a frozen policy-rollout dataset.
- AHA path: all 57 released REFLECT subset records and images were found; no final official AHA checkpoint is present in the release.

Passing a smoke test establishes executability, not reproduced paper metrics. Numerical claims enter the paper only after the fixed-seed episode protocol above is completed.
