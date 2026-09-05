"""Hash and structurally validate the four required original LIBERO suites."""
import hashlib
import json
import argparse
from pathlib import Path
import h5py

data = Path("/root/autodl-tmp/datasets/LIBERO-original")
root = Path(__file__).resolve().parents[1]
p = argparse.ArgumentParser()
p.add_argument("--suites", nargs="+", default=["libero_spatial", "libero_object", "libero_goal", "libero_10"])
p.add_argument("--output", default="manifests/libero-original-4suite.json")
a = p.parse_args()
rows = []
spec = json.loads((data / "source_spec.json").read_text())
expected_files = {x["rfilename"]: x for x in spec["files"]}
for suite in a.suites:
    paths = sorted((data / suite).glob("*.hdf5"))
    if len(paths) != 10:
        raise RuntimeError(f"{suite}: expected 10 complete HDF5 files, got {len(paths)}")
    for path in paths:
        digest = hashlib.sha256()
        with path.open("rb") as f:
            while chunk := f.read(8*1024*1024):
                digest.update(chunk)
        metadata = data / ".cache/huggingface/download" / suite / (path.name + ".metadata")
        lines = metadata.read_text().splitlines() if metadata.exists() else []
        expected = expected_files[f"{suite}/{path.name}"]
        assert digest.hexdigest() == expected["sha256"] and path.stat().st_size == expected["size"]
        if len(lines) >= 2 and len(lines[1]) == 64:
            assert digest.hexdigest() == lines[1], f"HF hash mismatch: {path}"
        with h5py.File(path) as h:
            demos = h["data"]
            lengths = []
            for key in demos:
                item = demos[key]
                actions = item["actions"]
                assert actions.ndim == 2 and actions.shape[1] == 7
                assert actions.shape[0] > 0
                assert "obs" in item
                lengths.append(actions.shape[0])
            row = dict(suite=suite, filename=path.name, bytes=path.stat().st_size,
                       sha256=digest.hexdigest(), revision=spec["revision"],
                       episodes=len(lengths), steps=sum(lengths), status="hash_and_structure_passed")
            rows.append(row)
            print(json.dumps(row), flush=True)
out = root / a.output
out.write_text(json.dumps(dict(source="yifengzhu-hf/LIBERO-datasets", files=rows,
                                total_bytes=sum(r["bytes"] for r in rows),
                                total_episodes=sum(r["episodes"] for r in rows)), indent=2))
