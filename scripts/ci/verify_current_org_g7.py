#!/usr/bin/env python3
"""Run unchanged G7 seven-case D0 readback against product-root ORG store.

Standalone, owner-review-only runner; *not* a trust/authorization gateway.
Call it from a separate, immutable exact PR19 source checkout.  This runner is
intentionally stored outside the source checkout and never rewrites source pins.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import unittest

EXACT_CHECKOUT = "93e6c84db1a061ee914aa2c1d543620404515c0b"
PRODUCT_MANIFEST_BLOB = "566b7210b6edb95a21b999dc1d881a12284d9011"
CURRENT_ORG_BLOB = "619fe224c05d7f7f7efe998583e4730cb2cb4d3e"
HISTORICAL_ORG_BLOB = "43ed448c02904ab44b3cf8665f4aeafb0a38f10a"
ORIGINAL_G7_BLOB = "6bd86d7972c8bca511b5702117be3542431e7493"
ORIGINAL_G7_PINS_BLOB = "cef9ce82a497522d2e4a9347b77453879e4790f3"
BACKEND = "product/ai-company-os-backend"
G7_PATH = "candidates/D5-G7/test_checkout.py"
G7_PINS_PATH = "candidates/D5-G7/SOURCE_PINS.json"
CURRENT_ORG_PATH = BACKEND + "/durable_ops.py"
OLD_ORG_PATH = "candidates/ORG-05R3/durable_ops.py"
EXPECTED_METHODS = (
    "test_current_org_head_drift",
    "test_exact_existing_readers_no_write",
    "test_forged_role_reference",
    "test_persisted_member_tamper",
    "test_revoked_iam",
    "test_wrong_expected_version",
    "test_wrong_latest_member",
)


class GateError(RuntimeError):
    """Fail-closed source or test gate; never treat as test PASS."""


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def safe_file(root: Path, relative: str) -> Path:
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise GateError("INVALID_PATH")
    rel = Path(relative)
    if rel.is_absolute() or any(p in ("", ".", "..") for p in rel.parts):
        raise GateError("TRAVERSAL_OR_ABSOLUTE_PATH")
    candidate = root
    for part in rel.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise GateError("SYMLINK_PATH_HOLD")
    if not candidate.is_file() or not candidate.resolve().is_relative_to(root.resolve()):
        raise GateError("MISSING_OR_ESCAPING_PATH")
    return candidate


def pinned_bytes(root: Path, rel: str, expected: str) -> bytes:
    raw = safe_file(root, rel).read_bytes()
    actual = git_blob(raw)
    if actual != expected:
        raise GateError(f"BLOB_MISMATCH:{rel}:{actual}")
    return raw


def check_commit(root: Path, expected: str = EXACT_CHECKOUT) -> None:
    if root.is_symlink() or not root.is_dir():
        raise GateError("INVALID_ROOT")
    command = ("git", "-C", str(root), "rev-parse", "--verify", "HEAD")
    completed = subprocess.run(command, capture_output=True, text=True, check=False, timeout=10)
    if completed.returncode or completed.stdout.strip() != expected:
        raise GateError("IMMUTABLE_COMMIT_MISMATCH")
    # No tracked edits: the current product must exactly equal Git's checkout.
    status = subprocess.run(("git", "-C", str(root), "status", "--porcelain", "--untracked-files=all"),
                            capture_output=True, text=True, check=False, timeout=20)
    if status.returncode or status.stdout.strip():
        raise GateError("NONCLEAN_CHECKOUT_HOLD")


def verify_manifest(root: Path) -> int:
    raw = pinned_bytes(root, "product/SOURCE_MANIFEST.json", PRODUCT_MANIFEST_BLOB)
    manifest = json.loads(raw.decode("utf-8"))
    files = manifest.get("files")
    if type(files) is not dict or len(files) != 561:
        raise GateError("MANIFEST_ENTRY_COUNT_HOLD")
    seen = set()
    for rel, meta in files.items():
        if not isinstance(meta, dict) or type(meta.get("bytes")) is not int or type(meta.get("sha256")) is not str:
            raise GateError("MALFORMED_MANIFEST")
        path = safe_file(root / "product", rel)
        raw_file = path.read_bytes()
        if len(raw_file) != meta["bytes"] or hashlib.sha256(raw_file).hexdigest() != meta["sha256"]:
            raise GateError("MANIFEST_CONTENT_MISMATCH:" + rel)
        seen.add(path.relative_to(root / "product").as_posix())
    actual = set()
    for p in (root / "product").rglob("*"):
        if p.is_symlink():
            raise GateError("PRODUCT_SYMLINK_HOLD")
        if p.is_file():
            actual.add(p.relative_to(root / "product").as_posix())
    if actual != seen | {"SOURCE_MANIFEST.json"} or len(actual) != 562:
        raise GateError("ORPHAN_OR_MISSING_PRODUCT_PATH")
    return len(files)


def verify_original_pins(root: Path) -> int:
    raw = pinned_bytes(root, G7_PINS_PATH, ORIGINAL_G7_PINS_BLOB)
    pins = json.loads(raw.decode("utf-8"))
    if type(pins) is not dict or len(pins) != 56:
        raise GateError("G7_PINSET_COUNT_HOLD")
    for rel, expected in pins.items():
        if type(expected) is not str or len(expected) != 40:
            raise GateError("INVALID_G7_PIN")
        pinned_bytes(root, rel, expected)
    pinned_bytes(root, G7_PATH, ORIGINAL_G7_BLOB)
    pinned_bytes(root, CURRENT_ORG_PATH, CURRENT_ORG_BLOB)
    pinned_bytes(root, OLD_ORG_PATH, HISTORICAL_ORG_BLOB)
    return len(pins)


@contextmanager
def product_import_first(root: Path):
    """Pin Python's current ORG module before historical G7 fixture prepends paths."""
    if "durable_ops" in sys.modules:
        raise GateError("PRELOADED_ORG_UNTRUSTED")
    backend = (root / BACKEND).resolve(strict=True)
    module_file = backend / "durable_ops.py"
    old_path = sys.path[:]
    try:
        sys.path.insert(0, str(backend))
        sys.path.insert(1, str(backend / "tests"))
        module = importlib.import_module("durable_ops")
        if Path(module.__file__).resolve() != module_file or module.OperationsStore.__module__ != "durable_ops":
            raise GateError("IMPORT_FALLBACK_TO_HISTORICAL_ORG")
        if git_blob(module_file.read_bytes()) != CURRENT_ORG_BLOB:
            raise GateError("LOADED_PRODUCT_ORG_BLOB_MISMATCH")
        yield module
    finally:
        sys.path[:] = old_path
        # Running in a dedicated child process is mandatory; do not reuse this interpreter.


def assert_fixture_uses_product(org_module, root: Path) -> None:
    fixture = sys.modules.get("test_org_core_checkout")
    if fixture is None or Path(fixture.__file__).resolve() != (root / "candidates/ORG-06/test_org_core_checkout.py").resolve():
        raise GateError("WRONG_ORG06_FIXTURE")
    if fixture.OperationsStore is not org_module.OperationsStore:
        raise GateError("FIXTURE_HAS_HISTORICAL_OPERATIONSSTORE")
    original = sys.modules.get("durable_ops")
    if original is not org_module or Path(original.__file__).resolve() != (root / CURRENT_ORG_PATH).resolve():
        raise GateError("G7_ORG_IMPORT_ORIGIN_CHANGED")


def run_g7(root: Path) -> dict:
    # Never create .pyc files in the verified immutable checkout.
    sys.dont_write_bytecode = True
    check_commit(root)
    manifest_count = verify_manifest(root)
    source_pin_count = verify_original_pins(root)
    if manifest_count != 561 or source_pin_count != 56:
        raise GateError("SOURCE_PREFLIGHT_HOLD")
    with product_import_first(root) as org_module:
        namespace = runpy.run_path(str(root / G7_PATH), run_name="__mi_p0_g7_current_org__")
        assert_fixture_uses_product(org_module, root)
        cls = namespace["ActualReadbackTests"]
        if unittest.TestLoader().getTestCaseNames(cls) != list(EXPECTED_METHODS):
            raise GateError("ORIGINAL_SEVEN_METHODS_CHANGED")
        cases = unittest.TestLoader().loadTestsFromTestCase(cls)
        output = io.StringIO()
        res = unittest.TextTestRunner(stream=output, verbosity=2).run(cases)
        sys.stderr.write(output.getvalue())
        if (res.testsRun != 7 or res.failures or res.errors or res.skipped or
            res.expectedFailures or res.unexpectedSuccesses or not res.wasSuccessful()):
            raise GateError("G7_CURRENT_PRODUCT_ORG_RUNTIME_NOT_PASS")
        return {
            "classification": "D0_SQLITE_CURRENT_PRODUCT_ORG_IMPORT_WITH_HISTORICAL_G7_TESTS",
            "checkout": EXACT_CHECKOUT,
            "current_org_git_blob": CURRENT_ORG_BLOB,
            "historical_org_git_blob": HISTORICAL_ORG_BLOB,
            "original_methods_unchanged": 7,
            "original_pin_records": source_pin_count,
            "product_manifest_verified": manifest_count,
            "tests_executed": res.testsRun,
            "tests_passed": res.testsRun,
            "tests_failed": 0,
            "tests_skipped": 0,
            "authenticated_issuer": "HOLD",
            "protected_postgres_restore": "NOT_RUN",
            "independent_security": "HOLD",
            "product_acceptance": "HOLD",
        }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="Separate exact 93e6c84 Git source checkout")
    parser.add_argument("--json-out", type=Path, default=None, help="Optional local evidence file outside source checkout")
    args = parser.parse_args(argv)
    try:
        result = run_g7(args.root.resolve())
        raw = json.dumps(result, sort_keys=True, indent=2) + "\n"
        print(raw, end="")
        if args.json_out is not None:
            dest = args.json_out.resolve()
            if dest.is_relative_to(args.root.resolve()):
                raise GateError("EVIDENCE_MUST_BE_OUTSIDE_CHECKOUT")
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(raw, encoding="utf-8")
        return 0
    except (GateError, OSError, ValueError, KeyError, ImportError, AssertionError, subprocess.SubprocessError) as exc:
        print("G7_CURRENT_ORG_HOLD: " + str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
