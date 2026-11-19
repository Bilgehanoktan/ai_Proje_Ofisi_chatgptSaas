"""MI-COMMON-04: recover *existing* immutable Model/Memory and 0207 Core bytes.

Retrieval helper only. Does not install packages, mutate product, authorize work,
start services, regenerate npm locks, execute tests, or promote a branch.
Source of truth: exact Git blob pins and original GitHub lock JSON objects.
"""
from __future__ import annotations

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import sys
import tempfile
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler

REPO = 'Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas'
SOURCE_COMMIT = '61bb06efbba7544bfc68260ed8eb4d342cab9b8e'
PIN_BLOBS = {
    'model': 'fb1a73c86eda928409c371359056e79ef43665e4',
    'core': '223f6fbd28cf4c428c07eb60dda4a36f644fa58c',
}
AUX_BLOBS = {
    'model': {
        'docs/master-integration/MI-07-08-JOINT-TRANSFER/run_combined.py': '6536c6571f5f9b3b3059bbd7e0ebc3089bc252bb',
        'docs/master-integration/MI-07-08-JOINT-TRANSFER/COMBINED_PINS.json': PIN_BLOBS['model'],
    },
    'core': {
        'tests/integration/run_core_0207.py': 'b019a5e60cfff4183b00e99f252ffe00bc164eda',
        'tests/integration/run_lifecycle_p05.py': 'befb9f429791a01b2fe37009e40f994a5924b2ff',
        'tests/integration/core_0207_source_lock.json': PIN_BLOBS['core'],
    },
}
MAX_BLOB_BYTES = 2_000_000


class SourceHold(RuntimeError):
    """A source/permission/environment mismatch, never a passing test."""


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()


def safe_rel(path: str) -> PurePosixPath:
    if (not isinstance(path, str) or not path or '\\' in path or ':' in path or '\x00' in path
            or path.startswith('/') or path.endswith('/') or '//' in path):
        raise SourceHold('UNSAFE_PIN_PATH')
    out = PurePosixPath(path)
    if out.as_posix() != path or any(x in ('.', '..') for x in path.split('/')):
        raise SourceHold('UNSAFE_PIN_PATH')
    return out


def verify_blob(data: bytes, blob: str, size: int | None = None,
                sha256: str | None = None) -> bytes:
    if (not isinstance(blob, str) or len(blob) != 40 or
            any(c not in '0123456789abcdef' for c in blob)):
        raise SourceHold('INVALID_PIN')
    if size is not None and len(data) != size:
        raise SourceHold('SIZE_MISMATCH:' + blob)
    if len(data) > MAX_BLOB_BYTES or git_blob(data) != blob:
        raise SourceHold('BLOB_PIN_MISMATCH:' + blob)
    if sha256 and hashlib.sha256(data).hexdigest() != sha256:
        raise SourceHold('SHA256_MISMATCH:' + blob)
    return data


def model_rows(raw: bytes) -> list[dict]:
    obj = json.loads(verify_blob(raw, PIN_BLOBS['model']))
    if not isinstance(obj, dict) or len(obj) != 114:
        raise SourceHold('MODEL_LOCK_SCOPE_HOLD')
    rows = []
    for path, info in obj.items():
        safe_rel(path)
        if not isinstance(info, dict) or not {'blob', 'bytes'} <= info.keys():
            raise SourceHold('MODEL_LOCK_FIELDS_HOLD')
        rows.append({'path': path, 'blob': info['blob'], 'bytes': info['bytes'],
                     'sha256': info.get('sha256')})
    return rows


def core_rows(raw: bytes) -> list[dict]:
    obj = json.loads(verify_blob(raw, PIN_BLOBS['core']))
    expected = {'test_retained_snapshot_0201': 5,
                'test_terminal_anchor_lifecycle_0203': 7,
                'test_lifecycle_projection_p02': 8,
                'test_lifecycle_prefix_p03': 9}
    if (len(obj.get('files', ())) != 55 or
            obj.get('source_commit') != '614aa63efbd0a95d0fa5fe47390df043d773370f' or
            {x['module']: x['count'] for x in obj.get('tests', [])} != expected or
            obj.get('direct_dependency_pins') != {
                'fastapi': '0.163.0', 'starlette': '1.10.0',
                'cryptography': '46.0.4', 'uvicorn': '0.34.2'}):
        raise SourceHold('CORE_LOCK_SCOPE_HOLD')
    rows = []
    for info in obj['files']:
        path = info['path']; safe_rel(path)
        rows.append({'path': path, 'blob': info['git_blob'], 'bytes': info['bytes'],
                     'sha256': info.get('sha256')})
    return rows


def normalize(rows: list[dict]) -> dict[str, dict]:
    by_path = {}
    for row in rows:
        path = row['path']; safe_rel(path)
        if path in by_path:
            raise SourceHold('DUPLICATE_PIN_PATH:' + path)
        if (not isinstance(row['bytes'], int) or row['bytes'] < 0 or
                row['bytes'] > MAX_BLOB_BYTES):
            raise SourceHold('UNSAFE_PIN_SIZE:' + path)
        by_path[path] = row
    return by_path


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise SourceHold('GITHUB_API_REDIRECT_HOLD')


class ExactCache:
    def __init__(self, root: Path, offline: bool = False, token: str = '',
                 opener=None):
        self.root = root
        self.offline = offline
        self.token = token
        self.opener = opener or build_opener(NoRedirect())

    def read(self, blob: str) -> bytes:
        # A reusable cache is addressable *only* by immutable Git blob SHA.
        validate_sha(blob)
        p = self.root/blob
        if p.is_symlink():
            raise SourceHold('CACHE_SYMLINK_HOLD:' + blob)
        if p.exists():
            data = p.read_bytes()
            return verify_blob(data, blob)
        if self.offline:
            raise SourceHold('CACHE_MISS_OFFLINE:' + blob)
        url = f'https://api.github.com/repos/{REPO}/git/blobs/{blob}'
        headers = {'Accept': 'application/vnd.github+json',
                   'X-GitHub-Api-Version': '2022-11-28',
                   'User-Agent': 'aicos-pinned-recovery-01'}
        if self.token:
            headers['Authorization'] = 'Bearer ' + self.token
        try:
            with self.opener.open(Request(url, headers=headers), timeout=15) as resp:
                if resp.status != 200:
                    raise SourceHold('GITHUB_RESPONSE_NOT_OK:' + blob)
                data = resp.read(MAX_BLOB_BYTES * 2 + 10000)
                if len(data) > MAX_BLOB_BYTES * 2 + 9999:
                    raise SourceHold('GITHUB_RESPONSE_OVERSIZE:' + blob)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            # Never print URLs with credentials or response bodies.
            raise SourceHold('GITHUB_FETCH_HOLD:' + blob + ':' + type(exc).__name__) from exc
        try:
            obj = json.loads(data)
            if (obj.get('sha') != blob or obj.get('encoding') != 'base64' or
                    not isinstance(obj.get('content'), str)):
                raise SourceHold('GITHUB_BLOB_RESPONSE_HOLD:' + blob)
            raw = base64.b64decode(obj['content'], validate=False)
            if len(raw) != obj.get('size'):
                raise SourceHold('GITHUB_BLOB_SIZE_HOLD:' + blob)
        except (ValueError, KeyError, TypeError) as exc:
            raise SourceHold('GITHUB_BLOB_FORMAT_HOLD:' + blob) from exc
        verify_blob(raw, blob)
        self.root.mkdir(parents=True, exist_ok=True)
        # Exclusive create; another writer may already have saved identical bytes.
        try:
            with p.open('xb') as f:
                f.write(raw)
        except FileExistsError:
            verify_blob(p.read_bytes(), blob)
        return raw


def validate_sha(value: str) -> None:
    if (not isinstance(value, str) or len(value) != 40 or
            any(c not in '0123456789abcdef' for c in value)):
        raise SourceHold('INVALID_BLOB_SHA')


def ensure_fresh(stage: Path, cache: Path) -> None:
    if stage.exists() or stage.is_symlink():
        raise SourceHold('DESTINATION_EXISTS_HOLD')
    if stage == cache or stage in cache.parents or cache in stage.parents:
        raise SourceHold('CACHE_STAGE_OVERLAP_HOLD')


def checked_write(root: Path, rel: str, raw: bytes) -> None:
    safe_rel(rel)
    path = root / rel
    if not path.absolute().is_relative_to(root.absolute()):
        raise SourceHold('UNSAFE_DESTINATION')
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or path.exists():
        raise SourceHold('DESTINATION_COLLISION:' + rel)
    with path.open('xb') as f:
        f.write(raw)


def recover(cache: ExactCache, stage: Path, modes: tuple[str, ...], workers: int = 6,
            *, pins_override: dict[str, bytes] | None = None,
            aux_override: dict[str, dict[str, str]] | None = None) -> dict:
    ensure_fresh(stage, cache.root)
    locks = {}
    rows = {}
    for mode in modes:
        raw = pins_override[mode] if pins_override and mode in pins_override else cache.read(PIN_BLOBS[mode])
        locks[mode] = raw
        rows[mode] = normalize(model_rows(raw) if mode == 'model' else core_rows(raw))
    aux = aux_override or {mode: AUX_BLOBS[mode] for mode in modes}
    # Verify the overlap among original 0207 and current Memory *before* staging.
    overlapping, differing = [], []
    if set(modes) == {'model', 'core'}:
        overlapping = sorted(set(rows['model']) & set(rows['core']))
        differing = [x for x in overlapping if rows['model'][x]['blob'] != rows['core'][x]['blob']]
        if len(overlapping) != 26 or len(differing) != 2:
            raise SourceHold('HISTORICAL_OVERLAY_SCOPE_HOLD')
    requests = {}
    for mode in modes:
        for row in rows[mode].values():
            requests[row['blob']] = None
        for blob in aux[mode].values():
            requests[blob] = None
    for mode, raw in locks.items():
        requests[PIN_BLOBS[mode]] = raw
    count = 0
    # All required bytes must resolve and pass hash checks before writing any staged file.
    with ThreadPoolExecutor(max_workers=max(1, min(8, workers))) as pool:
        futures = {pool.submit(cache.read, blob): blob for blob in sorted(requests)
                   if requests[blob] is None}
        for fut in as_completed(futures):
            blob = futures[fut]
            requests[blob] = fut.result()
            count += 1
    for mode in modes:
        for row in rows[mode].values():
            verify_blob(requests[row['blob']], row['blob'], row['bytes'], row.get('sha256'))
        for blob in aux[mode].values():
            verify_blob(requests[blob], blob)
    staging = stage.with_name(stage.name + '.partial')
    if staging.exists():
        raise SourceHold('PARTIAL_STAGE_EXISTS_HOLD')
    staging.mkdir(parents=True, exist_ok=False)
    try:
        for mode in modes:
            out = staging/mode
            for row in rows[mode].values():
                checked_write(out, row['path'], requests[row['blob']])
            for path, blob in aux[mode].items():
                # Pin-manifest rows sometimes already contain the auxiliary path.
                if path not in rows[mode]:
                    checked_write(out, path, requests[blob])
                elif rows[mode][path]['blob'] != blob:
                    raise SourceHold('AUX_SOURCE_COLLISION_HOLD:' + path)
        report = {
            'revision': 'MI-COMMON-04-PINNED-RECOVERY',
            'source_commit': SOURCE_COMMIT, 'status': 'RECOVERED_NOT_TESTED',
            'modes': list(modes),
            'model_pin_count': len(rows.get('model', {})),
            'core_pin_count': len(rows.get('core', {})),
            'overlap_paths': len(overlapping), 'historical_changed_paths': differing,
            'unique_git_blobs': len(requests),
            'resolved_blob_reads': count,
            'test_runs': {'model_344': 'NOT_RUN', 'core_29': 'NOT_RUN',
                          'w8_full_build': 'NOT_RUN', 'browser': 'NOT_RUN'},
            'independent_acceptance': 'HOLD', 'protected_commit': 'HOLD'
        }
        checked_write(staging, 'RECOVERY_EVIDENCE.json',
                      (json.dumps(report, indent=2, ensure_ascii=False) + '\n').encode())
        staging.rename(stage)
        return report
    except BaseException:
        # Failure cannot leave a stage that looks complete. Keep partial bytes for diagnosis.
        raise


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--cache', type=Path, required=True, help='Fresh or audited Git-blob SHA cache')
    ap.add_argument('--stage', type=Path, required=True, help='New stage; must not exist')
    ap.add_argument('--mode', choices=['model', 'core', 'both'], default='both')
    ap.add_argument('--offline', action='store_true', help='No network requests, refuse cache misses')
    ap.add_argument('--workers', type=int, default=6)
    ap.add_argument('--evidence', type=Path, help='Fresh report file outside stage')
    args = ap.parse_args()
    modes = ('model', 'core') if args.mode == 'both' else (args.mode,)
    report = {'revision': 'MI-COMMON-04-PINNED-RECOVERY',
              'source_commit': SOURCE_COMMIT, 'status': 'HOLD',
              'modes': list(modes), 'test_runs': {'model_344': 'NOT_RUN',
                                                'core_29': 'NOT_RUN',
                                                'w8_full_build': 'NOT_RUN',
                                                'browser': 'NOT_RUN'}}
    try:
        if args.evidence and args.evidence.exists():
            raise SourceHold('EVIDENCE_EXISTS_HOLD')
        root = args.stage.resolve(strict=False)
        cache_root = args.cache.resolve(strict=False)
        cache = ExactCache(cache_root, offline=args.offline,
                           token=os.environ.get('GITHUB_TOKEN') or os.environ.get('GH_TOKEN') or '')
        report = recover(cache, root, modes, workers=args.workers)
    except (SourceHold, ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as exc:
        report['reason'] = str(exc)
    if args.evidence:
        args.evidence.parent.mkdir(parents=True, exist_ok=True)
        with args.evidence.open('x', encoding='utf8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
            f.write('\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report['status'] == 'RECOVERED_NOT_TESTED' else 2


if __name__ == '__main__':
    sys.exit(main())
