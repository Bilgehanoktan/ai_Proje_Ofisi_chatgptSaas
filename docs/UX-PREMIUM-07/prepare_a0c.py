"""Prepare an exact A0C source and W8 review stage; never approve or install."""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys

REPO = 'https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas.git'
COMMIT = 'a79df6622e2eb9de63795ff6c0309984d1be6910'
PINS = {
    'product/SOURCE_MANIFEST.json': 'f5b011cc9f72e85a7d1c371705e11e6dacfc9c42',
    'tests/integration/w8_ux_a0c.py': '52ac6add8b0bc338527e9e12c7848c9056d8f836',
}
RUNNER = 'tests/integration/w8_ux_a0c.py'


def run(args, cwd=None, capture=False):
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', NEXT_TELEMETRY_DISABLED='1')
    result = subprocess.run([str(a) for a in args], cwd=cwd, env=env, check=True,
                            text=True, stdout=subprocess.PIPE if capture else None)
    return result.stdout.strip() if capture else None


def git_blob(path):
    raw = path.read_bytes()
    return hashlib.sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()


def checkout_exact(source, repo, commit):
    if source.exists() or source.is_symlink():
        raise ValueError('SOURCE_ALREADY_EXISTS')
    run(['git', 'init', '--quiet', '--template=', source])
    def git(*args, capture=False):
        return run(['git', '-C', source, *args], capture=capture)
    git('config', '--local', 'core.longpaths', 'true')
    git('config', '--local', 'core.autocrlf', 'false')
    git('remote', 'add', 'origin', repo)
    git('fetch', '--no-tags', '--depth=1', 'origin', commit)
    if git('rev-parse', 'FETCH_HEAD', capture=True) != commit:
        raise ValueError('FETCH_HEAD_MISMATCH')
    git('checkout', '--detach', commit)
    if git('rev-parse', 'HEAD', capture=True) != commit:
        raise ValueError('CHECKOUT_COMMIT_MISMATCH')
    if git('status', '--porcelain', '--untracked-files=no', capture=True):
        raise ValueError('DIRTY_TRACKED_CHECKOUT')


def prepare(workspace, repo=REPO, commit=COMMIT, pins=PINS, audit_only=False):
    root = workspace.expanduser().absolute()
    if root.exists() or root.is_symlink():
        raise ValueError('WORKSPACE_ALREADY_EXISTS; choose a new directory')
    root.mkdir(parents=True, exist_ok=False)
    root = root.resolve(strict=True)
    source, stage = root/'src', root/'stage'
    print('SOURCE:', source, flush=True)
    checkout_exact(source, repo, commit)
    for name, pin in pins.items():
        path = source/name
        if path.is_symlink() or not path.is_file() or git_blob(path) != pin:
            raise ValueError('SOURCE_PIN_HOLD: '+name)
    runner = source/RUNNER
    run([sys.executable, runner, 'audit'], cwd=source)
    print('EXACT_SOURCE_AUDIT_PASS', flush=True)
    if audit_only:
        return None
    run([sys.executable, runner, 'prepare', '--stage', stage], cwd=source)
    review = stage/'locks/REVIEW.json'
    if not review.is_file() or review.is_symlink():
        raise ValueError('REVIEW_MISSING_HOLD')
    fingerprint = hashlib.sha256(review.read_bytes()).hexdigest()
    print('REVIEW_REQUIRED:', review, flush=True)
    print('REVIEW_SHA256:', fingerprint, flush=True)
    print('STOP: inspect locks, transitive versions and wheel provenance before approval.', flush=True)
    return fingerprint


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--workspace', type=Path, required=True,
                        help='New short directory; never reuse previous UI/Premium stages')
    parser.add_argument('--audit-only', action='store_true')
    args = parser.parse_args()
    try:
        prepare(args.workspace, audit_only=args.audit_only)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print('HOLD:', exc, file=sys.stderr)
        print('Preserve diagnostics; retry with a fresh workspace.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
