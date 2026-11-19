#!/usr/bin/env python3
"""AI Company OS MI-05: exact local checkout + isolated Model/Memory and Core stage.

Source archive, Git tree and pin checks only. No installs, build, browser, tests,
real permissions, external providers, DB mutation, or deployment.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from zipfile import ZipFile, BadZipFile

REPO = 'Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas'
ARCHIVE_COMMIT = '87272b6aebd1ce4b26d3a789b2ea75e4310cf60a'
EXPECTED_GIT_TREE = '187f652f1b1ff8604981833f634c4531a33f8a47'
EXPECTED_FILES = 1953
EXPECTED_UNCOMPRESSED = 22_342_956
MAX_ZIP_BYTES = 100_000_000
MAX_UNCOMPRESSED = 80_000_000
MAX_FILE_BYTES = 16_000_000
MODEL_PIN_PATH = 'docs/master-integration/MI-07-08-JOINT-TRANSFER/COMBINED_PINS.json'
MODEL_PIN_BLOB = 'fb1a73c86eda928409c371359056e79ef43665e4'
CORE_PIN_PATH = 'tests/integration/core_0207_source_lock.json'
CORE_PIN_BLOB = '223f6fbd28cf4c428c07eb60dda4a36f644fa58c'
HELPER_PATH = 'docs/master-integration/MI-COMMON-04-PINNED-RECOVERY/pinned_source_recovery.py'
HELPER_BLOB = '70c9c0970632834a2c4ba9cd4e4d718bfc14c2b4'
MANIFEST_PATH = 'product/SOURCE_MANIFEST.json'
MANIFEST_BLOB = '03af243e8683f92c5d9c0b24e90b70d2bd6af29f'
HIST_PREFIX = 'tests/integration/historical_0207/'
BACKEND_PREFIX = 'product/ai-company-os-backend/'
ARCHIVE_URL = f'https://github.com/{REPO}/archive/{ARCHIVE_COMMIT}.zip'


class TransferHold(RuntimeError):
    """A safety or provenance condition prevents completion."""


def object_sha(kind: str, data: bytes) -> str:
    return hashlib.sha1((kind + ' ' + str(len(data))).encode('ascii') + b'\0' + data).hexdigest()


def safe_name(name: str) -> str:
    if (not name or name.startswith('/') or name.endswith('/') or '\\' in name
            or ':' in name or '\x00' in name or '//' in name):
        raise TransferHold('UNSAFE_ARCHIVE_PATH:' + name[:90])
    p = PurePosixPath(name)
    if p.as_posix() != name or any(x in ('.', '..') for x in name.split('/')):
        raise TransferHold('UNSAFE_ARCHIVE_PATH:' + name[:90])
    return name


def tree_sha(files: dict[str, bytes]) -> str:
    """Reconstruct exact Git 100644 blob/040000 tree for audited repository."""
    root: dict[str, object] = {}
    for name, data in files.items():
        safe_name(name)
        node = root
        parts = name.split('/')
        for segment in parts[:-1]:
            if segment in node and not isinstance(node[segment], dict):
                raise TransferHold('FILE_DIRECTORY_CONFLICT:' + segment)
            node = node.setdefault(segment, {})
        if parts[-1] in node:
            raise TransferHold('DUPLICATE_TREE_ENTRY:' + name)
        node[parts[-1]] = object_sha('blob', data)

    def walk(node: dict[str, object]) -> str:
        pieces = []
        ordered = sorted(node.items(), key=lambda item: (item[0] + ('/' if isinstance(item[1], dict) else '')).encode('utf-8'))
        for name, content in ordered:
            is_dir = isinstance(content, dict)
            sha = walk(content) if is_dir else content
            mode = b'40000' if is_dir else b'100644'
            pieces.append(mode + b' ' + name.encode('utf-8') + b'\0' + bytes.fromhex(sha))
        return object_sha('tree', b''.join(pieces))

    return walk(root)


def read_archive(path: Path, *, expected_tree: str = EXPECTED_GIT_TREE,
                 expected_count: int = EXPECTED_FILES,
                 expected_bytes: int = EXPECTED_UNCOMPRESSED) -> tuple[dict[str, bytes], str]:
    if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_ZIP_BYTES:
        raise TransferHold('ARCHIVE_MISSING_OR_OVERSIZE')
    files: dict[str, bytes] = {}
    roots = set()
    total = 0
    with ZipFile(path) as archive:
        for item in archive.infolist():
            if item.is_dir():
                continue
            name = item.filename
            if '/' not in name:
                raise TransferHold('ARCHIVE_ROOT_MISSING')
            root, rel = name.split('/', 1)
            if not (root.startswith('ai_Proje_Ofisi_chatgptSaas-') or root.startswith('Bilgehanoktan-ai_Proje_Ofisi_chatgptSaas-')):
                raise TransferHold('UNEXPECTED_ARCHIVE_ROOT')
            roots.add(root)
            safe_name(rel)
            if rel in files:
                raise TransferHold('DUPLICATE_ZIP_MEMBER:' + rel)
            mode = (item.external_attr >> 16) & 0o170000
            if mode not in (0, stat.S_IFREG):
                raise TransferHold('UNEXPECTED_ZIP_MODE:' + rel)
            if item.file_size > MAX_FILE_BYTES or item.file_size < 0:
                raise TransferHold('ZIP_MEMBER_OVERSIZE:' + rel)
            total += item.file_size
            if total > MAX_UNCOMPRESSED or len(files) >= 5000:
                raise TransferHold('ZIP_TOTAL_OVERSIZE')
            data = archive.read(item)
            if len(data) != item.file_size:
                raise TransferHold('ZIP_CONTENT_SIZE_MISMATCH:' + rel)
            files[rel] = data
    if len(roots) != 1 or len(files) != expected_count or total != expected_bytes:
        raise TransferHold('ARCHIVE_SCOPE_HOLD:' + str([len(roots), len(files), total]))
    observed = tree_sha(files)
    if observed != expected_tree:
        raise TransferHold('GIT_TREE_PIN_MISMATCH:' + observed)
    return files, observed


def archive_download(path: Path) -> None:
    """HTTPS archive only, no API rate limit or token; resulting ZIP still hash audited."""
    req = Request(ARCHIVE_URL, headers={'User-Agent': 'aios-mi05-verified-local-checkout', 'Accept': 'application/zip'})
    try:
        with urlopen(req, timeout=90) as resp:
            final = urlparse(resp.geturl())
            if final.scheme != 'https' or final.hostname not in {'github.com', 'codeload.github.com'}:
                raise TransferHold('ARCHIVE_REDIRECT_HOST_HOLD')
            count = 0
            with path.open('xb') as out:
                while True:
                    data = resp.read(1024 * 1024)
                    if not data:
                        break
                    count += len(data)
                    if count > MAX_ZIP_BYTES:
                        raise TransferHold('ARCHIVE_DOWNLOAD_OVERSIZE')
                    out.write(data)
    except Exception as exc:
        if isinstance(exc, TransferHold):
            raise
        raise TransferHold('ARCHIVE_DOWNLOAD_FAILED:' + type(exc).__name__) from exc


def _verified_asset(files: dict[str, bytes], path: str, blob: str, byte_count: int | None = None,
                    sha256: str | None = None) -> bytes:
    value = files.get(path)
    if value is None or (byte_count is not None and len(value) != byte_count):
        raise TransferHold('PINNED_FILE_MISSING_OR_SIZE:' + path)
    if object_sha('blob', value) != blob or (sha256 and hashlib.sha256(value).hexdigest() != sha256):
        raise TransferHold('PINNED_FILE_CHANGED:' + path)
    return value


def seed_cache(files: dict[str, bytes], cache: Path, recovery) -> dict:
    model_lock = _verified_asset(files, MODEL_PIN_PATH, MODEL_PIN_BLOB)
    core_lock = _verified_asset(files, CORE_PIN_PATH, CORE_PIN_BLOB)
    helper = _verified_asset(files, HELPER_PATH, HELPER_BLOB)
    _verified_asset(files, MANIFEST_PATH, MANIFEST_BLOB)
    model_rows = recovery.normalize(recovery.model_rows(model_lock))
    core_rows = recovery.normalize(recovery.core_rows(core_lock))
    if len(model_rows) != 114 or len(core_rows) != 55:
        raise TransferHold('ORIGINAL_LOCK_COUNT_HOLD')
    overlaps = set(model_rows) & set(core_rows)
    differing = sorted(p for p in overlaps if model_rows[p]['blob'] != core_rows[p]['blob'])
    if len(overlaps) != 26 or len(differing) != 2:
        raise TransferHold('CORE_HISTORY_COLLISION_HOLD')
    cache.mkdir(parents=True, exist_ok=False)
    bytes_by_sha: dict[str, bytes] = {}
    history = []

    def record(path: str, blob: str, size: int | None = None, sha: str | None = None,
               *, historical: bool = False) -> None:
        try:
            raw = _verified_asset(files, path, blob, size, sha)
        except TransferHold:
            if not historical or not path.startswith(BACKEND_PREFIX):
                raise
            historical_path = HIST_PREFIX + path[len(BACKEND_PREFIX):]
            raw = _verified_asset(files, historical_path, blob, size, sha)
            history.append({'original': path, 'archive': historical_path})
        present = bytes_by_sha.get(blob)
        if present is not None and present != raw:
            raise TransferHold('BLOB_COLLISION_HOLD:' + blob)
        bytes_by_sha[blob] = raw

    for row in model_rows.values():
        record(row['path'], row['blob'], row['bytes'], row.get('sha256'))
    for row in core_rows.values():
        record(row['path'], row['blob'], row['bytes'], row.get('sha256'), historical=True)
    for mode, aux in recovery.AUX_BLOBS.items():
        for path, blob in aux.items():
            record(path, blob)
    # Insert the immutable pin documents and recovery helper in addressed cache.
    record(MODEL_PIN_PATH, MODEL_PIN_BLOB)
    record(CORE_PIN_PATH, CORE_PIN_BLOB)
    for blob, raw in bytes_by_sha.items():
        with (cache / blob).open('xb') as handle:
            handle.write(raw)
    return {'model_rows': len(model_rows), 'core_rows': len(core_rows),
            'overlapping_paths': len(overlaps), 'differing_paths': differing,
            'historical_overlay_used': history, 'cached_blobs': len(bytes_by_sha),
            'model_without_sha256': sum(not x.get('sha256') for x in model_rows.values()),
            'core_without_sha256': sum(not x.get('sha256') for x in core_rows.values()),
            'recovery_helper_blob': object_sha('blob', helper)}


def run(output: Path, archive: Path | None = None, *, minimum_free: int = 130_000_000) -> dict:
    if sys.version_info < (3, 10):
        raise TransferHold('PYTHON_3_10_OR_NEWER_REQUIRED')
    output = output.resolve(strict=False)
    if output.exists() or output.is_symlink():
        raise TransferHold('DESTINATION_ALREADY_EXISTS:' + str(output))
    if not output.parent.is_dir() or output.parent.is_symlink():
        raise TransferHold('DESTINATION_PARENT_MISSING')
    if shutil.disk_usage(output.parent).free < minimum_free:
        raise TransferHold('INSUFFICIENT_DISK_SPACE_130MB')
    partial = output.with_name(output.name + '.partial')
    if partial.exists() or partial.is_symlink():
        raise TransferHold('INCOMPLETE_PRIOR_STAGE_EXISTS:' + str(partial))
    partial.mkdir(parents=True)
    try:
        destination_zip = partial / 'source_commit.zip'
        if archive is None:
            archive_download(destination_zip)
        else:
            origin = archive.resolve(strict=True)
            if not origin.is_file() or origin == destination_zip or origin.is_symlink():
                raise TransferHold('INVALID_USER_ARCHIVE')
            shutil.copyfile(origin, destination_zip)
        files, git_tree = read_archive(destination_zip, expected_tree=EXPECTED_GIT_TREE,
                                       expected_count=EXPECTED_FILES,
                                       expected_bytes=EXPECTED_UNCOMPRESSED)
        helper_path = partial / 'pinned_source_recovery.py'
        helper_path.write_bytes(_verified_asset(files, HELPER_PATH, HELPER_BLOB))
        spec = importlib.util.spec_from_file_location('aicos_mi04_exact_recovery', helper_path)
        if spec is None or spec.loader is None:
            raise TransferHold('EXACT_HELPER_IMPORT_HOLD')
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        cache = partial / 'git_blob_cache'
        cache_record = seed_cache(files, cache, helper)
        # Extract the full exact source tree; do not materialize unverified archives.
        checkout = partial / 'full_checkout'
        checkout.mkdir()
        for name, data in files.items():
            target = checkout.joinpath(*name.split('/'))
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open('xb') as handle:
                handle.write(data)
        staged = partial / 'pinned_regression_stage'
        original_result = helper.recover(helper.ExactCache(cache, offline=True), staged, ('model', 'core'))
        if original_result['status'] != 'RECOVERED_NOT_TESTED':
            raise TransferHold('UPSTREAM_STAGE_HOLD')
        result = {
            'revision': 'MI-05-LOCAL-VERIFIED-CHECKOUT',
            'status': 'SOURCE_RECOVERED_TESTS_NOT_RUN',
            'archive_commit': ARCHIVE_COMMIT,
            'git_tree': git_tree,
            'archive_sha256': hashlib.sha256(destination_zip.read_bytes()).hexdigest(),
            'archive_bytes': destination_zip.stat().st_size,
            'checkout_files_verified': len(files),
            'checkout_uncompressed_bytes': sum(map(len, files.values())),
            'source_manifest_blob': MANIFEST_BLOB,
            **cache_record,
            'upstream_recovery': original_result,
            'paths': {'full_checkout': 'full_checkout', 'model_stage': 'pinned_regression_stage/model',
                      'core_stage': 'pinned_regression_stage/core',
                      'original_zip': 'source_commit.zip'},
            'tests': {'model_memory_344': 'NOT_RUN', 'historical_core_29': 'NOT_RUN',
                      'full_w8_build': 'NOT_RUN', 'browser': 'NOT_RUN'},
            'permissions': {'protected_commit': 'HOLD', 'independent_acceptance': 'HOLD',
                            'ci': 'DISABLED', 'external_provider': 'DISABLED'},
        }
        (partial / 'TRANSFER_REPORT.json').write_text(json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        partial.rename(output)
        return result
    except BaseException as exc:
        try:
            (partial / 'TRANSFER_HOLD.json').write_text(json.dumps({
                'status': 'HOLD', 'error_type': type(exc).__name__, 'reason': str(exc),
                'archive_commit': ARCHIVE_COMMIT}, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        except OSError:
            pass
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path, help='NEW destination folder; parent must exist')
    parser.add_argument('--archive', type=Path, help='Previously downloaded exact commit ZIP (for private repositories)')
    args = parser.parse_args()
    try:
        out = run(args.output, args.archive)
        print(json.dumps({'status': out['status'], 'git_tree': out['git_tree'],
                          'verified_checkout_files': out['checkout_files_verified'],
                          'model_files': out['model_rows'], 'core_files': out['core_rows'],
                          'overlay_paths': len(out['historical_overlay_used']),
                          'report': str(args.output / 'TRANSFER_REPORT.json')}, ensure_ascii=False, indent=2))
        return 0
    except (TransferHold, OSError, ValueError, KeyError, TypeError, BadZipFile) as exc:
        print('HOLD:', type(exc).__name__, str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
