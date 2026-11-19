"""Exact source-locked GATE02 Core/ORG readback runner; never a grant.

Usage: python -I -B run_original_core_assignment.py /path/to/EXACT_Gate03_checkout
No downloads; no installs; no source writes. Exit 2 on preflight HOLD, 1 on test failure.
"""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from importlib.metadata import version, PackageNotFoundError

HERE = Path(__file__).resolve().parent
PINS = json.loads((HERE / 'SOURCE_PINS.json').read_text(encoding='utf-8'))
PREFIX = 'product/ai-company-os-backend/'

def blob(raw):
    return hashlib.sha1(f'blob {len(raw)}\0'.encode('ascii') + raw).hexdigest()

def require(condition, reason):
    if not condition:
        raise ValueError(reason)

def check_original_source(root):
    all_pins = PINS['source_paths']
    require(root.is_dir(), 'CHECKOUT_ROOT_MISSING')
    manifest = root / 'product' / 'SOURCE_MANIFEST.json'
    require(manifest.is_file() and not manifest.is_symlink(), 'MANIFEST_MISSING')
    raw = manifest.read_bytes()
    require(blob(raw) == PINS['manifest_git_blob'], 'MANIFEST_BLOB_MISMATCH')
    info = json.loads(raw)
    entries = info['files']
    require(len(entries) == 552, 'OWNER_552_MANIFEST_EXPECTED')
    for rel, expected in all_pins.items():
        path = root / rel
        require(path.is_file() and not path.is_symlink(), f'ABSENT_SOURCE {rel}')
        require(blob(path.read_bytes()) == expected, f'EXACT_SOURCE_BLOB_MISMATCH {rel}')
        if rel.startswith('product/'):
            key = rel[len('product/'):]
            item = entries.get(key)
            require(item is not None, f'OWNER_MANIFEST_MISSING {rel}')
            raw = path.read_bytes()
            require(item['bytes'] == len(raw) and item['sha256'] == hashlib.sha256(raw).hexdigest(),
                    f'OWNER_MANIFEST_SHA_MISMATCH {rel}')
    return len(all_pins)

def main():
    require(len(sys.argv) == 2, 'EXACT_OWNER_CHECKOUT_ROOT_REQUIRED')
    root = Path(sys.argv[1]).expanduser().resolve()
    require((sys.version.split()[0], sqlite3.sqlite_version) == ('3.13.5', '3.46.1'),
            'PINNED_PYTHON_SQLITE_ENVIRONMENT_REQUIRED')
    require(version('cryptography') == '46.0.4', 'PINNED_CRYPTOGRAPHY_REQUIRED')
    n = check_original_source(root)
    backend = root / PREFIX
    # Only a copy of the new test is involved; the original product tree stays read-only.
    snippet = '''import sys,unittest\nsys.path[:0] = sys.argv[1:]\nsuite=unittest.defaultTestLoader.loadTestsFromName("test_assignment_original_core_readback")\nassert suite.countTestCases()==4, suite.countTestCases()\nresult=unittest.TextTestRunner(verbosity=2).run(suite)\nprint("ACTUAL_CORE_ASSIGNMENT=", result.testsRun, "fail=", len(result.failures), "err=", len(result.errors), "skip=",len(result.skipped), flush=True)\nsys.exit(0 if result.wasSuccessful() and result.testsRun==4 and not result.skipped else 1)\n'''
    cp = subprocess.run([sys.executable, '-I', '-B', '-c', snippet,
                         str(HERE / 'tests'), str(backend), str(backend / 'tests')],
                        cwd=root, check=False)
    require(check_original_source(root) == n, 'SOURCE_CHANGED_AFTER_TEST')
    print(f'EXACT_OWNER_SOURCES={n}/{n} OWNER=GATE03', flush=True)
    print('PRODUCT_ACCEPTANCE=HOLD; OWNER_APPROVAL=HOLD; ORIGINAL_T1_FULLCHAIN=NOT_RUN', flush=True)
    return cp.returncode

if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError, PackageNotFoundError) as exc:
        print('PREFLIGHT_BLOCKED', str(exc), flush=True)
        sys.exit(2)
