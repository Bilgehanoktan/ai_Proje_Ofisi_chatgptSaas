#!/usr/bin/env python3
"""Export pinned AIOS R4 source tree; no product execution, install or remote write."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import tempfile
import zipfile

REMOTE = 'https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas.git'
COMMIT = '1ac127144515496dd7e70d940c76a3122a4a0570'
SUBTREE = 'candidates/H01-LOCAL-DELIVERY-20261125/INTEGRATED-REVIEW/source'
TREE = '78593080158f644114c6ce2739a985ba1fde8217'
PRODUCT = '2440b9e2d3f513f2789feb634066655847101828'
MANIFEST = '3de94145197137fb60506fc05dfa23bbee00c208'
FILE_COUNT = 1915
MANIFEST_COUNT = 583


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def blob(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode('ascii') + b'\0' + raw).hexdigest()


def tree_files(repo, tree):
    result = {}
    for item in git(repo, 'ls-tree', '-r', '-z', tree).split(b'\0'):
        if not item:
            continue
        info, path = item.split(b'\t', 1)
        mode, kind, oid = info.decode('ascii').split()
        name = path.decode('utf-8')
        pure = PurePosixPath(name)
        if (mode != '100644' or kind != 'blob' or name in result or pure.is_absolute()
                or pure.as_posix() != name or '..' in pure.parts or '\\' in name or ':' in name):
            raise ValueError('UNSAFE_OR_UNEXPECTED_TREE_ENTRY: ' + name)
        result[name] = oid
    return result


def verify_zip(path, expected, manifest_blob, manifest_count):
    with zipfile.ZipFile(path) as z:
        entries = [i for i in z.infolist() if not i.is_dir()]
        names = [i.filename for i in entries]
        if len(names) != len(set(names)) or set(names) != set(expected):
            raise ValueError('ARCHIVE_FILE_SET_MISMATCH')
        if z.testzip() is not None:
            raise ValueError('ARCHIVE_CRC_HOLD')
        mpath = 'product/SOURCE_MANIFEST.json'
        raw = z.read(mpath)
        if blob(raw) != manifest_blob or expected.get(mpath) != manifest_blob:
            raise ValueError('MANIFEST_BLOB_MISMATCH')
        pins = json.loads(raw)['files']
        if type(pins) is not dict or len(pins) != manifest_count:
            raise ValueError('MANIFEST_COUNT_MISMATCH')
        wanted = {'product/' + p for p in pins} | {mpath}
        if {n for n in names if n.startswith('product/')} != wanted:
            raise ValueError('PRODUCT_FILE_SET_MISMATCH')
        for name in names:
            data = z.read(name)
            if blob(data) != expected[name]:
                raise ValueError('GIT_BLOB_MISMATCH: ' + name)
            if name.startswith('product/') and name != mpath:
                pin = pins[name.removeprefix('product/')]
                if len(data) != pin['bytes'] or hashlib.sha256(data).hexdigest() != pin['sha256']:
                    raise ValueError('PRODUCT_SHA256_MISMATCH: ' + name)
    return {'git_blobs_verified': len(names), 'product_manifest_verified': len(pins)}


def export(repo, output):
    if git(repo, 'rev-parse', COMMIT + ':' + SUBTREE).decode().strip() != TREE:
        raise ValueError('R4_SOURCE_TREE_MISMATCH')
    if git(repo, 'rev-parse', TREE + ':product').decode().strip() != PRODUCT:
        raise ValueError('R4_PRODUCT_TREE_MISMATCH')
    expected = tree_files(repo, TREE)
    if len(expected) != FILE_COUNT:
        raise ValueError('R4_FILE_COUNT_MISMATCH')
    if output.exists():
        raise FileExistsError(str(output))
    with tempfile.TemporaryDirectory(prefix='aios-export-', dir=output.parent) as tmp:
        staging = Path(tmp) / 'source.zip'
        git(repo, 'archive', '--format=zip', '--output=' + str(staging), TREE)
        result = verify_zip(staging, expected, MANIFEST, MANIFEST_COUNT)
        digest = hashlib.sha256()
        with staging.open('rb') as f:
            for block in iter(lambda: f.read(1024 * 1024), b''):
                digest.update(block)
        # Exclusive publication: never overwrite a user's existing archive.
        with output.open('xb') as dest, staging.open('rb') as src:
            for block in iter(lambda: src.read(1024 * 1024), b''):
                dest.write(block)
        return dict(result, commit=COMMIT, source_tree=TREE, product_tree=PRODUCT,
                    manifest_blob=MANIFEST, archive=output.name, bytes=output.stat().st_size,
                    sha256=digest.hexdigest(), source_integrity='PASS',
                    original_git_checkout=False, runtime='NOT_RUN', acceptance='HOLD')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, help='Existing local Git repository containing pinned commit')
    parser.add_argument('--output', type=Path, default=Path('AIOS_R4_EXACT_SOURCE.zip'))
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.parent.is_dir() or output.exists():
        raise ValueError('OUTPUT_PARENT_OR_EXISTING_FILE_HOLD')
    if args.repo:
        result = export(args.repo.resolve(), output)
    else:
        # Read-only remote fetch into disposable bare repo, using existing Git authentication.
        # No checkout, hooks, package installation, workflow dispatch, credentials in output or push.
        with tempfile.TemporaryDirectory(prefix='aios-r4-fetch-') as tmp:
            repo = Path(tmp)
            git(repo, 'init', '--bare', '--quiet')
            git(repo, 'fetch', '--no-tags', '--no-recurse-submodules', '--depth=1', REMOTE, COMMIT)
            result = export(repo, output)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
        raise SystemExit('SOURCE_EXPORT_HOLD: ' + type(exc).__name__ + ': ' + str(exc))
