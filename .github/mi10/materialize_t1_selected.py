"""MI-10 CI helper: materialize the existing 30 pinned D0 T1 replay inputs.

This is not a new security implementation, integration approval, or test oracle.
It preserves exact original GATE-01 test and product bytes in disposable storage.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

EXPECTED_COMMON = "61bb06efbba7544bfc68260ed8eb4d342cab9b8e"
EXPECTED_OWNER = "6bab62305d2ea15f8608f7835270ae027ce01e83"
EXPECTED_EVIDENCE = "878a0e4f2eb105353c7ce9b072797b17142517f2"
EVIDENCE_PATH = "docs/master-integration/MI-03-GATE01-AUTHORITY-API-REVIEW-01"
OWNER_SUFFIXES = {
    "product/ai-company-os-backend/app/core/transaction/intent_authority.py",
    "product/ai-company-os-backend/app/core/iam_session.py",
}

def assert_checkout(root: Path, expected: str) -> None:
    got = subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    if got != expected:
        raise RuntimeError("SOURCE_COMMIT_HOLD: " + str(root))

def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

def run() -> None:
    if len(sys.argv) != 2:
        raise ValueError("USAGE: materialize_t1_selected.py OUTPUT_DIR")
    workspace = Path(os.environ["GITHUB_WORKSPACE"]).resolve()
    common, owner, evidence = (workspace / x for x in ("candidate", "owner", "evidence"))
    for root, commit in (
        (common, EXPECTED_COMMON),
        (owner, EXPECTED_OWNER),
        (evidence, EXPECTED_EVIDENCE),
    ):
        assert_checkout(root, commit)
    folder = evidence / EVIDENCE_PATH
    pins = json.loads((folder / "T1_DIRECT_PINS.json").read_text("utf-8"))
    if len(pins) != 30 or set(OWNER_SUFFIXES) - set(pins):
        raise ValueError("T1_PIN_COUNT_OR_OWNER_HOLD")
    stage = Path(sys.argv[1]).resolve()
    if stage.exists() or stage.is_relative_to(workspace) or stage.is_symlink():
        raise ValueError("T1_STAGE_ISOLATION_HOLD")
    stage.mkdir(parents=True)
    for rel, expected in pins.items():
        if not rel or rel.startswith("/") or ".." in Path(rel).parts or "\\" in rel:
            raise ValueError("T1_UNSAFE_PATH_HOLD")
        src_root = owner if rel in OWNER_SUFFIXES else common
        source = src_root / rel
        if not source.is_file() or source.is_symlink():
            raise ValueError("T1_MISSING_SOURCE_HOLD " + rel)
        raw = source.read_bytes()
        actual = {
            "blob": git_blob(raw),
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        }
        if actual != expected:
            raise ValueError("T1_SOURCE_PIN_HOLD " + rel)
        dst = stage / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        with dst.open("xb") as output:
            output.write(raw)
    runner = folder / "run_t1_direct.py"
    if git_blob(runner.read_bytes()) != "84a0e23747aabc0b3dbe45e6958ff887979efc95":
        raise ValueError("T1_RUNNER_PIN_HOLD")
    print("T1_SOURCE_PRECHECK=30/30; EXTRA_PRODUCT_SOURCES=0", flush=True)
    subprocess.run([sys.executable, "-B", str(runner), str(stage)], check=True)
    print("T1_REPLAY_SCOPE=D0_SQLITE_ONLY; POSTGRES_IAM_ORG_COMMIT=NOT_RUN", flush=True)

if __name__ == "__main__":
    run()
