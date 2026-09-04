#!/usr/bin/env python3
"""Create a deterministic SHA-256 manifest for an experiment data directory."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--revision", default="unknown")
    args = parser.parse_args()

    root = args.root.expanduser().resolve(strict=True)
    output = args.output.expanduser().resolve()
    files = []
    for path in sorted(p for p in root.rglob("*") if p.is_file()):
        if ".cache" in path.parts:
            continue
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )

    manifest = {
        "root": str(root),
        "revision": args.revision,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "file_count": len(files),
        "total_bytes": sum(item["bytes"] for item in files),
        "files": files,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
