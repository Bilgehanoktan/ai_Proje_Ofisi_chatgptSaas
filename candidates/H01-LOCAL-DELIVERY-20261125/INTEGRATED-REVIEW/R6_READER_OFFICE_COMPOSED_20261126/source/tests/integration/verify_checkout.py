"""Full local byte-manifest and shared-file parity preflight. Never starts the product."""
from pathlib import Path
import hashlib, json, sys
root = Path(__file__).resolve().parents[2] / 'product'
manifest = json.loads((root/'SOURCE_MANIFEST.json').read_text(encoding='utf-8'))['files']
actual = {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and not any(part in {'node_modules','.next','__pycache__','.pytest_cache','.venv'} for part in p.relative_to(root).parts) and p.relative_to(root).as_posix() != 'SOURCE_MANIFEST.json'}
if actual != set(manifest):
    sys.exit(f'Paths differ: missing={sorted(set(manifest)-actual)}, extra={sorted(actual-set(manifest))}')
for path, pin in manifest.items():
    data=(root/path).read_bytes()
    if len(data)!=pin['bytes'] or hashlib.sha256(data).hexdigest()!=pin['sha256']:
        sys.exit(f'Byte mismatch: {path}')
f,b=root/'ai-company-os-frontend',root/'ai-company-os-backend'
for fp,bp in [(f/'contracts/generated',b/'contracts/source'),(f/'fixtures',b/'fixtures')]:
    for p in fp.glob('*.json'):
        q=bp/p.name
        if not q.is_file() or p.read_bytes()!=q.read_bytes(): sys.exit(f'Parity mismatch: {p.name}')
print(f'PASS {len(manifest)} source byte pins and shared schema/fixture parity')
