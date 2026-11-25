"""Read-only source integrity preflight. No product import, network, install or execution."""
import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def verify(root: Path, expected_blob: str) -> dict:
    product = root / 'product'
    manifest_path = product / 'SOURCE_MANIFEST.json'
    if product.is_symlink() or manifest_path.is_symlink():
        raise ValueError('SYMLINK_ROOT')
    raw = manifest_path.read_bytes()
    if git_blob(raw) != expected_blob:
        raise ValueError('MANIFEST_GIT_BLOB_MISMATCH')
    manifest = json.loads(raw)
    files = manifest['files']
    if not isinstance(files, dict) or not files:
        raise ValueError('MANIFEST_FILES_INVALID')
    expected = set()
    for name, pin in files.items():
        path = PurePosixPath(name)
        if (not name or '\\' in name or ':' in name or path.is_absolute() or path.as_posix() != name
                or '..' in path.parts or name == 'SOURCE_MANIFEST.json'):
            raise ValueError('UNSAFE_PATH: ' + name)
        if (type(pin.get('bytes')) is not int or pin['bytes'] < 0
                or not re.fullmatch('[0-9a-f]{64}', pin.get('sha256', ''))):
            raise ValueError('INVALID_PIN: ' + name)
        target = product.joinpath(*path.parts)
        if any(p.is_symlink() for p in (target, *target.parents) if p == product or product in p.parents):
            raise ValueError('SYMLINK: ' + name)
        data = target.read_bytes()
        if len(data) != pin['bytes'] or hashlib.sha256(data).hexdigest() != pin['sha256']:
            raise ValueError('SOURCE_BYTES_MISMATCH: ' + name)
        expected.add(name)
    actual = set()
    for p in product.rglob('*'):
        if p.is_symlink():
            raise ValueError('UNEXPECTED_SYMLINK: ' + str(p))
        if p.is_file():
            actual.add(p.relative_to(product).as_posix())
    if actual != expected | {'SOURCE_MANIFEST.json'}:
        raise ValueError('SOURCE_SET_MISMATCH: extra=' + repr(sorted(actual - expected - {'SOURCE_MANIFEST.json'}))
                         + ' missing=' + repr(sorted(expected - actual)))
    return {'source_manifest_blob': expected_blob, 'verified_files': len(expected),
            'product_files': len(actual), 'source_integrity': 'MATCH',
            'runtime': 'NOT_RUN', 'authorization': 'NOT_EVALUATED'}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True, help='Extracted repository root')
    parser.add_argument('--manifest-blob', required=True, help='Pinned 40-char Git manifest blob')
    args = parser.parse_args()
    try:
        if not re.fullmatch('[0-9a-f]{40}', args.manifest_blob):
            raise ValueError('INVALID_MANIFEST_BLOB')
        print(json.dumps(verify(args.root.resolve(), args.manifest_blob), indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as exc:
        print('PREFLIGHT_HOLD:', exc)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
