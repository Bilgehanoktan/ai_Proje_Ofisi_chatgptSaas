"""MEM-05E exact selected synthetic regression; no real provider or PG/CI."""
import hashlib
import json
from pathlib import Path
import sqlite3
import sys
import unittest

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parents[1] / 'product' / 'ai-company-os-backend'
PINS = HERE / 'LOCAL_PINS.json'
EXPECTED = 184
MODULES = ['test_memory_gateway_recovery_w5_mem05e', 'test_memory_recovery_w5_mem05d',
           'test_memory_history_w5_mem03', 'test_memory_checkpoint_w5_mem04',
           'test_memory_gateway_05c_r2', 'test_memory_gateway_05c_r1', 'test_router_cost_review',
           'test_memory_access_0194', 'test_memory_store_0196', 'test_runtime_memory_model_0207',
           'test_joint_context_0208', 'test_memory_witness_0209']


def verify():
    pins = json.loads(PINS.read_text(encoding='utf-8'))
    if len(pins) != 50:
        raise ValueError('PIN_COUNT_MISMATCH')
    for rel, expected in sorted(pins.items()):
        p = BACKEND / rel
        if p.is_symlink() or not p.is_file() or not p.resolve().is_relative_to(BACKEND.resolve()):
            raise ValueError('PATH_MISMATCH: ' + rel)
        data = p.read_bytes()
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode('ascii') + b'\0' + data).hexdigest()
        if (len(data), hashlib.sha256(data).hexdigest(), blob) != (expected['bytes'], expected['sha256'], expected['blob']):
            raise ValueError('SOURCE_MISMATCH: ' + rel)
    print('SOURCE_PINS=50/50', flush=True)


def main():
    try:
        verify()
        import cryptography
        print('PYTHON=' + sys.version, flush=True)
        print('SQLITE=' + sqlite3.sqlite_version, flush=True)
        print('CRYPTOGRAPHY=' + cryptography.__version__, flush=True)
        sys.path[:0] = [str(BACKEND), str(BACKEND/'tests')]
        suite = unittest.defaultTestLoader.loadTestsFromNames(MODULES)
        if suite.countTestCases() != EXPECTED:
            raise ValueError('TEST_COUNT_MISMATCH: ' + str(suite.countTestCases()))
    except Exception as exc:
        print('BLOCKED: ' + str(exc), flush=True)
        return 2
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print('TESTS_RUN=' + str(result.testsRun), flush=True)
    print('FAILURES=' + str(len(result.failures)), flush=True)
    print('ERRORS=' + str(len(result.errors)), flush=True)
    print('SKIPPED=' + str(len(result.skipped)), flush=True)
    try:
        verify()
    except Exception as exc:
        print('POSTCHECK_BLOCKED: ' + str(exc), flush=True)
        return 2
    code = int(not (result.wasSuccessful() and result.testsRun == EXPECTED and not result.skipped))
    print('EXIT_CODE=' + str(code), flush=True)
    return code


if __name__ == '__main__':
    sys.exit(main())
