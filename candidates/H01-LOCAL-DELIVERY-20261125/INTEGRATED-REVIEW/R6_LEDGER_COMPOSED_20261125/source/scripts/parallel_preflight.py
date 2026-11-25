"""Offline three-way Git blob inventory comparison; never writes or merges a repo."""
import json
import re
import sys
from pathlib import Path, PurePosixPath

SHARED = frozenset({'AGENTS.md', 'PROJECT_INDEX.md', 'product/SOURCE_MANIFEST.json',
                    'docs/architecture/DESIGN_MASTER.md', 'catalog/TECHNICAL_CATALOG.md'})

def shared(path):
    return (path in SHARED or path.startswith(('handover/', 'progress/', 'security/', 'decisions/'))
            or '/contracts/' in path or path.startswith('database/'))

def validate(inventory):
    if not isinstance(inventory, dict):
        raise ValueError('INVENTORY_TYPE')
    seen = set()
    for path, blob in inventory.items():
        if not isinstance(path, str) or not isinstance(blob, str):
            raise ValueError('ENTRY_TYPE')
        p = PurePosixPath(path)
        if (not path or path == '.' or p.is_absolute() or '..' in p.parts or '\\' in path
                or p.as_posix() != path or path.casefold() in seen):
            raise ValueError('UNSAFE_OR_ALIAS_PATH')
        if not re.fullmatch(r'[0-9a-f]{40}', blob):
            raise ValueError('GIT_BLOB_PIN')
        seen.add(path.casefold())

def compare(base, local, incoming):
    """Inputs must be complete inventories of commits with a verified common ancestor."""
    for inventory in (base, local, incoming):
        validate(inventory)
    rows = []
    for path in sorted(set(base) | set(local) | set(incoming)):
        b, l, r = base.get(path), local.get(path), incoming.get(path)
        if l == r == b:
            continue
        if l == r:
            status = 'SAME_CHANGE'
        elif r == b:
            status = 'LOCAL_ONLY'
        elif l == b:
            status = 'INCOMING_ONLY'
        else:
            status = 'DIVERGED'
        deletion = b is not None and (l is None or r is None)
        manual = shared(path) or deletion or status == 'DIVERGED'
        rows.append({'path': path, 'base': b, 'local': l, 'incoming': r,
                     'status': status, 'manual_review': manual})
    aliases = {}
    for path in sorted(set(local) | set(incoming)):
        aliases.setdefault(path.casefold(), []).append(path)
    collisions = [names for names in aliases.values() if len(names) > 1]
    return {'status': 'REVIEW_REQUIRED', 'rows': rows, 'case_collisions': collisions,
            'manual_count': sum(row['manual_review'] for row in rows),
            'merge_authorized': False}

if __name__ == '__main__':
    if len(sys.argv) != 4:
        raise SystemExit('usage: parallel_preflight.py BASE.json LOCAL.json INCOMING.json')
    inputs = [json.loads(Path(p).read_text(encoding='utf-8')) for p in sys.argv[1:]]
    print(json.dumps(compare(*inputs), indent=2, ensure_ascii=False))
