"""Pin and download official I-FailSense 1-view assets; never print credentials."""
import hashlib
import json
from pathlib import Path
from huggingface_hub import HfApi, snapshot_download

DEST = Path('/root/autodl-tmp/models/ifailsense')
DEST.mkdir(parents=True, exist_ok=True)
api = HfApi()
specs = [('model', 'google/paligemma2-3b-mix-224'),
         ('model', 'ACIDE/FailSense-Calvin-1p-3b'),
         ('dataset', 'ACIDE/AHA-Calvin-1p')]
manifest_path = DEST / 'asset_manifest_v1.json'
if manifest_path.exists():
    manifest = json.loads(manifest_path.read_text())
else:
    manifest = []
    for kind, repo in specs:
        info = api.repo_info(repo, repo_type=kind, files_metadata=True)
        files = [dict(path=s.rfilename, size=s.size) for s in info.siblings]
        manifest.append(dict(repo=repo, kind=kind, revision=info.sha, files=files))
    manifest_path.write_text(json.dumps(manifest, indent=2))
for item in manifest:
    info = api.repo_info(item['repo'], repo_type=item['kind'], revision=item['revision'], files_metadata=True)
    for record in item['files']:
        sibling = next(x for x in info.siblings if x.rfilename == record['path'])
        if sibling.lfs:
            record['sha256'] = sibling.lfs['sha256']
    print(json.dumps(dict(repo=item['repo'], revision=item['revision'])), flush=True)
    # Evaluation uses only validation; do not fetch the unneeded training split.
    patterns = ['*.json', '*.model', '*.safetensors', '*.txt'] if item['kind'] == 'model' else ['*validation*.parquet', '*.json', 'README.md']
    try:
        snapshot = snapshot_download(item['repo'], repo_type=item['kind'], revision=item['revision'], allow_patterns=patterns, max_workers=2)
    except Exception as error:
        # Signed CDN URLs must not be copied into publication evidence.
        print('Download failed: ' + type(error).__name__, flush=True)
        raise SystemExit(1)
    for record in item['files']:
        path = Path(snapshot) / record['path']
        if not path.is_file():
            continue
        assert path.stat().st_size == record['size'], record['path']
        if 'sha256' in record:
            hasher = hashlib.sha256()
            with path.open('rb') as stream:
                for block in iter(lambda: stream.read(8 * 1024 * 1024), b''):
                    hasher.update(block)
            assert hasher.hexdigest() == record['sha256'], 'Hash mismatch: ' + record['path']
            record['verified_sha256'] = hasher.hexdigest()
    item['snapshot'] = snapshot
    print('Completed ' + item['repo'], flush=True)
    manifest_path.write_text(json.dumps(manifest, indent=2))
