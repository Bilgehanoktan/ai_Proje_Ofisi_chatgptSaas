#!/usr/bin/env python3
"""Recover existing pinned AI Company OS sources using Git; no merge, build or tests.
Uses the user's normal Git authentication. Produces one ZIP of exact tree ZIPs + receipt.
No credentials are requested, read, exported or written by this script.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import tempfile
import zipfile

URL = 'https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas.git'
PINS = {
    'canonical': ('integration/product-dev', '254e0188998d0d245bd8ee4eb901aead02951a66', 'fac62a73dab9c06f71cb3be19bf0ccf34b0ba572'),
    'PR31': ('review/mi-p0-566-g2g9-officeproxy-source-20261120', '316d2dd86d245fd8f04bdb6921c57eafe63c590a', 'aa61f2d6a573f2f83475c8580b2f486a270e608a'),
    'PR46': ('review/mi-p0-nw02-iam-session-binding-d0-20261122', '098486f272047a4fef8ba07b90738f2baeb5351e', '3294c4336223b2d70c8397f613451b760406547a'),
    'PR47': ('review/03api-core-plan-read-pin-20261122', 'a647095f57c319210596a3552dfacf40a37baf2d', '5348b07b7769692117a3cae984ed2d4a53be5c3a'),
    'PR49': ('integration/mi05-ui03-readstatus-presentation-r3-20261123', '9a74c398f2fff65d57254f7de3a0e00a70dda90d', 'c8d06f5b13a90ea36f92a4816ed8d9c05baf2349'),
    'PR19': ('review/mi04-g2-on-553-isolated-compat-20261120', '0a8907f177bb3e9b458aefb3ea3441b15537f542', '20c14563ea2970b0dbaedf6ed9181b8adf211be4'),
    'PR54': ('review/nw07-scheduler-state-version-20261124', '41dc540b43546854b9e0b6e2d855bffe5fdd965a', '7f5359a76f065ed10c79d20a34e7ef38135ea101'),
    'PR38': ('review/mi01-w8-certifi-20261120-c50-r2-20261121', '0ce023ea53e6aed4938528941ebe4fa37c7da6d4', '8ce26debf7b9eb295b1ad354522ebede460d43ad'),
    'PR50': ('review/mi05-office-mime-token-owner-handoff-20261123', '596282284a9b29216a89a7cc20651b3b31c501bd', '06d8a6ea81aeb3ffb3feb4865e0d5607ee00a4b8'),
    'PR51': ('review/mi-p0-proxy-mime-token-owner-handoff-20261123', 'c12567aed7d8f20aab9c4162471cfc97808c5d0d', 'a7c18312c5e8633b4cd8ec1c1662bdb291c1ab9d'),
}
CANONICAL_MANIFEST = '27b4eb5816265d4e6e6d2458acb6220db7dd0c76'
HANDOFF_DIR = 'candidates/MI05-CEO-RUNTIME-ORG-R2-20261125/source-recovery/'
HANDOFF_FILES = {HANDOFF_DIR + 'AIOS_EXACT_SOURCE_RECOVERY_20261125.py', HANDOFF_DIR + 'RECOVERY_VALIDATION.json'}


def git(repo, *args):
    command = ['git', '-C', str(repo), *args]
    p = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if p.returncode:
        # Avoid copying Git credential-helper output into evidence or chat.
        raise RuntimeError(f'GIT_COMMAND_FAILED: {args[0]} (exit {p.returncode})')
    return p.stdout


def digest(data):
    return hashlib.sha256(data).hexdigest()


def blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def file_digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def safe_path(name):
    p = PurePosixPath(name)
    if not name or p.is_absolute() or p.as_posix() != name or '\\' in name or ':' in name or any(x in ('.', '..') for x in p.parts):
        raise ValueError('UNSAFE_TREE_PATH')
    return name


def tree_entries(repo, sha):
    raw = git(repo, 'ls-tree', '-r', '-z', '--full-tree', sha)
    entries = {}
    for line in raw.split(b'\0'):
        if not line:
            continue
        header, path = line.split(b'\t', 1)
        mode, kind, object_id = header.decode('ascii').split()
        name = safe_path(path.decode('utf-8'))
        if kind != 'blob' or mode not in ('100644', '100755') or name in entries:
            raise ValueError('UNSUPPORTED_TREE_ENTRY: ' + name)
        entries[name] = (mode, object_id)
    return entries


def manifest_review(z, verified):
    name = 'product/SOURCE_MANIFEST.json'
    if name not in verified:
        return {'status': 'HOLD', 'reason': 'MANIFEST_MISSING'}
    try:
        source = json.loads(z.read(name))['files']
        if not isinstance(source, dict):
            raise ValueError('manifest files must be mapping')
        actual = {p[len('product/'):]: info for p, info in verified.items() if p.startswith('product/') and p != name}
        missing = sorted(set(actual) - set(source))
        extra = sorted(set(source) - set(actual))
        mismatch = sorted(p for p in set(source) & set(actual) if not isinstance(source[p], dict) or source[p].get('bytes') != actual[p]['bytes'] or source[p].get('sha256') != actual[p]['sha256'])
        return {'status': 'PASS' if not (missing or extra or mismatch) else 'HOLD', 'entries': len(source), 'actual': len(actual), 'missing_from_manifest': missing, 'not_in_tree': extra, 'byte_hash_mismatch': mismatch, 'blob': verified[name]['git_blob']}
    except (ValueError, TypeError, KeyError, UnicodeError):
        return {'status': 'HOLD', 'reason': 'MANIFEST_INVALID'}


def exact_archive(repo, sha, expected_tree, out):
    actual_tree = git(repo, 'rev-parse', sha + '^{tree}').decode('ascii').strip()
    if actual_tree != expected_tree:
        raise ValueError('TREE_SHA_MISMATCH')
    entries = tree_entries(repo, sha)
    git(repo, 'archive', '--format=zip', '--output=' + str(out), sha)
    verified = {}
    with zipfile.ZipFile(out) as z:
        names = [safe_path(i.filename) for i in z.infolist() if not i.is_dir()]
        if len(set(names)) != len(names) or set(names) != set(entries):
            raise ValueError('ARCHIVE_PATH_SET_MISMATCH')
        for n in names:
            data = z.read(n)  # CRC verified by zipfile.
            mode, expected_blob = entries[n]
            info = z.getinfo(n)
            actual_mode = (info.external_attr >> 16) & 0o177777
            mode_ok = actual_mode == int(mode, 8) or (mode == '100644' and info.create_system == 0 and actual_mode == 0)
            if blob(data) != expected_blob or not mode_ok:
                raise ValueError('ARCHIVE_BLOB_OR_MODE_MISMATCH: ' + n)
            verified[n] = {'git_blob': expected_blob, 'bytes': len(data), 'sha256': digest(data), 'mode': mode}
        manifest = manifest_review(z, verified)
    # Preserve case-sensitive archive; flag extraction risks instead of overwriting files.
    folded = {}
    for n in verified:
        folded.setdefault(n.casefold(), []).append(n)
    collisions = [v for v in folded.values() if len(v) > 1]
    return {'commit': sha, 'tree': expected_tree, 'archive_sha256': file_digest(out), 'file_count': len(verified), 'raw_bytes': sum(v['bytes'] for v in verified.values()), 'archive_integrity': 'PASS', 'manifest': manifest, 'case_collisions': collisions, 'files': verified}


def remote_heads(repo, selected):
    refs = ['refs/heads/' + PINS[n][0] for n in selected]
    raw = git(repo, 'ls-remote', '--heads', URL, *refs).decode('ascii')
    result = {ref: sha for sha, ref in (line.split('\t') for line in raw.splitlines() if line)}
    for n in selected:
        branch, sha, _ = PINS[n]
        observed = result.get('refs/heads/' + branch, '')
        if observed != sha and (n != 'PR49' or len(observed) != 40 or any(c not in '0123456789abcdef' for c in observed)):
            raise ValueError('REMOTE_HEAD_DRIFT_OR_MISSING: ' + n)
    return result


def verify_fetched_head(repo, name, observed):
    _, pinned, _ = PINS[name]
    actual = git(repo, 'rev-parse', 'refs/heads/recovery/' + name).decode('ascii').strip()
    if actual != observed:
        raise ValueError('FETCHED_HEAD_DRIFT: ' + name)
    if actual == pinned:
        return
    # The script's own single evidence-only publication may advance PR49.
    # Never accept a source change, rebase, merge, or other drift. Archive pinned bytes.
    if name != 'PR49':
        raise ValueError('FETCHED_HEAD_DRIFT: ' + name)
    header = git(repo, 'cat-file', '-p', actual).split(b'\n\n', 1)[0].splitlines()
    parents = [line.split()[1].decode('ascii') for line in header if line.startswith(b'parent ')]
    raw = git(repo, 'diff-tree', '--no-commit-id', '-r', '--name-status', '-z', '--no-renames', pinned, actual).split(b'\0')
    items = raw[:-1] if raw[-1] == b'' else raw
    if parents != [pinned] or len(items) != 2 * len(HANDOFF_FILES) or any(items[i] != b'A' for i in range(0, len(items), 2)) or {items[i].decode('utf-8') for i in range(1, len(items), 2)} != HANDOFF_FILES:
        raise ValueError('PR49_NON_HANDOFF_HEAD_DRIFT')


def recover(selected, output):
    if output.exists() or output.is_symlink():
        raise ValueError('OUTPUT_ALREADY_EXISTS')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='aios-exact-source-') as tmp:
        root = Path(tmp).resolve()
        repo = root / 'objects.git'
        git(root, 'init', '--bare', str(repo))
        before = remote_heads(repo, selected)
        refs = ['refs/heads/' + PINS[n][0] + ':refs/heads/recovery/' + n for n in selected]
        git(repo, 'fetch', '--no-tags', '--depth=2', '--atomic', URL, *refs)
        receipt = {'status': 'SOURCE_RECOVERY_ONLY', 'repository': URL, 'heads_before': before, 'snapshots': {}, 'tests': 'NOT_RUN', 'integration': 'HOLD', 'security_acceptance': 'HOLD'}
        for n in selected:
            branch, sha, tree = PINS[n]
            verify_fetched_head(repo, n, before['refs/heads/' + branch])
            archive = root / (n + '.zip')
            info = exact_archive(repo, sha, tree, archive)
            if n == 'canonical' and (info['file_count'] != 1858 or info['manifest'].get('blob') != CANONICAL_MANIFEST or info['manifest']['status'] != 'PASS' or info['manifest'].get('entries') != 552):
                raise ValueError('CANONICAL_SOURCE_OR_MANIFEST_HOLD')
            receipt['snapshots'][n] = info
            print(f"{n}: {info['file_count']} exact files; manifest {info['manifest']['status']}", flush=True)
        receipt['heads_after'] = remote_heads(repo, selected)
        if receipt['heads_after'] != before:
            raise ValueError('REMOTE_HEAD_CHANGED_DURING_RECOVERY')
        # ZIPs already compressed; do not recompress their contents.
        package = root / 'AIOS_EXACT_SOURCE_BUNDLE.zip'
        with zipfile.ZipFile(package, 'w', compression=zipfile.ZIP_STORED) as z:
            for n in selected:
                z.write(root / (n + '.zip'), n + '.zip')
            z.writestr('SOURCE_RECOVERY_RECEIPT.json', json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', compress_type=zipfile.ZIP_DEFLATED)
        with zipfile.ZipFile(package) as z:
            if z.testzip() is not None:
                raise ValueError('BUNDLE_CRC_HOLD')
        # Exclusive creation: never overwrite an existing user file.
        with package.open('rb') as source, output.open('xb') as destination:
            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                destination.write(chunk)
        if file_digest(output) != file_digest(package):
            raise ValueError('OUTPUT_COPY_HASH_MISMATCH')
        print('SOURCE_RECOVERY_PASS (archive only, not product acceptance)')
        print('FILE:', output)
        print('SHA256:', file_digest(output))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--targets', nargs='+', choices=list(PINS), default=list(PINS))
    ap.add_argument('--output', type=Path, default=Path.home() / 'Downloads' / 'AIOS_EXACT_SOURCE_BUNDLE_20261125.zip')
    args = ap.parse_args()
    try:
        recover(list(dict.fromkeys(args.targets)), args.output.expanduser().absolute())
    except (OSError, ValueError, RuntimeError, zipfile.BadZipFile) as exc:
        print('HOLD:', str(exc))
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
