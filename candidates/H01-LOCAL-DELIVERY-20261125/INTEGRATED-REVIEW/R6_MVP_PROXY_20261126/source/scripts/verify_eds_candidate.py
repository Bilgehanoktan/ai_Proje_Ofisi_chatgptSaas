"""Offline exact Git-blob preflight; no product import or execution."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re


def verify(root, manifest):
    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        raise ValueError('candidate root must be a real directory')
    expected = {}
    for item in manifest['files']:
        raw = item['path']
        path = PurePosixPath(raw)
        if not raw or path.is_absolute() or '\\' in raw or ':' in raw or any(p in ('', '.', '..') for p in raw.split('/')) or raw in expected:
            raise ValueError('invalid or duplicate manifest path')
        if not re.fullmatch(r'[0-9a-f]{40}', item['sha']) or type(item['size']) is not int or item['size'] < 0:
            raise ValueError('invalid manifest hash or size')
        expected[raw] = item
    if not expected:
        raise ValueError('empty manifest')
    if len({p.casefold() for p in expected}) != len(expected):
        raise ValueError('case-colliding manifest paths')
    actual = set()
    errors = []
    for path in root.rglob('*'):
        name = path.relative_to(root).as_posix()
        if path.is_symlink():
            errors.append(f'SYMLINK:{name}')
        elif path.is_file():
            actual.add(name)
        elif not path.is_dir():
            errors.append(f'NOT_REGULAR:{name}')
    errors.extend(f'MISSING:{p}' for p in sorted(expected.keys()-actual))
    errors.extend(f'EXTRA:{p}' for p in sorted(actual-expected.keys()))
    matched = 0
    for name in sorted(actual & expected.keys()):
        p = root / name
        item = expected[name]
        if p.stat().st_size != item['size']:
            errors.append(f'SIZE:{name}')
            continue
        data = p.read_bytes()
        digest = hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
        if digest != item['sha']:
            errors.append(f'HASH:{name}')
        else:
            matched += 1
    return {'status':'PASS' if not errors else 'HOLD','expected':len(expected),'matched':matched,'errors':errors,'product_execution':False,'authority':'NOT_GRANTED_BY_PREFLIGHT'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--manifest', required=True, type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.root, json.loads(args.manifest.read_text(encoding='utf-8')))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result = {'status':'HOLD','errors':[str(exc)],'product_execution':False,'authority':'NOT_GRANTED_BY_PREFLIGHT'}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
