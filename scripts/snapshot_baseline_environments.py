"""Record runtime versions without exporting credentials or environment secrets."""
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / "docs/reproduction/results/20260905"
out.mkdir(parents=True, exist_ok=True)
packages = ["torch", "torchvision", "transformers", "numpy", "scipy", "scikit-learn", "wandb", "hydra-core", "omegaconf", "robosuite", "mujoco", "gymnasium", "mani_skill", "sapien", "mplib", "opencv-python", "h5py"]
records = {}
for env in ("openvla-oft", "ava-vla", "vla-safe", "wcm", "maniskill3"):
    script = "import importlib.metadata as m,json,sys; names=" + repr(packages) + "; installed={d.metadata['Name'].lower().replace('_','-') for d in m.distributions()}; print(json.dumps({'python':sys.version,'versions':{p:m.version(p) if p.lower().replace('_','-') in installed else None for p in names}}))"
    records[env] = json.loads(subprocess.check_output([f"/root/autodl-tmp/conda-envs/{env}/bin/python", "-c", script], text=True))
records["gpu"] = subprocess.check_output(["nvidia-smi", "--query-gpu=name,driver_version,memory.total", "--format=csv,noheader"], text=True).strip()
(out / "environment_versions.json").write_text(json.dumps(records, indent=2))
print("Saved version audit", out / "environment_versions.json")
