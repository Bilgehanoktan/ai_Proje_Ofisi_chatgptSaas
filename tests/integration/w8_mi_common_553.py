"""Review-only W8 adapter for the exact 553-file MI03 common source candidate.

Keeps the original 539 W8 adapter byte-identical and all its dependency,
approval, source and browser gates in place. Not a new CI or acceptance grant.
"""
from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys

PARENT = "w8_mi_common_02.py"
PARENT_GIT_BLOB = "acd361f17331f512ce35a1611e8108d32e61680f"
PARENT_MANIFEST_BLOB = "03af243e8683f92c5d9c0b24e90b70d2bd6af29f"
CANDIDATE_MANIFEST_BLOB = "27b4eb5816265d4e6e6d2458acb6220db7dd0c76"
CANDIDATE_COMMIT = "a80932b6d5e99667889dfaa25b682feb267c6cba"


def git_blob(raw: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(raw)).encode("ascii") + b"\0" + raw).hexdigest()


def load_pinned_parent(path: Path):
    """No symlink, hash drift or dynamic fallback to unrelated local modules."""
    if path.is_symlink() or not path.is_file():
        raise ValueError("MI01_553_PARENT_FILE_HOLD")
    if git_blob(path.read_bytes()) != PARENT_GIT_BLOB:
        raise ValueError("MI01_553_PARENT_PIN_HOLD")
    spec = importlib.util.spec_from_file_location("mi01_553_original_w8", path)
    if spec is None or spec.loader is None:
        raise ValueError("MI01_553_IMPORT_HOLD")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module.MANIFEST != PARENT_MANIFEST_BLOB:
        raise ValueError("MI01_553_OLD_MANIFEST_HOLD")
    return module


def load_candidate():
    original = load_pinned_parent(Path(__file__).resolve().with_name(PARENT))
    # Only the exact source manifest identity changes: no skipped tests,
    # replaced dependency approval, changed authority or altered source files.
    original.MANIFEST = CANDIDATE_MANIFEST_BLOB
    w8 = original.load_candidate()
    if w8.MANIFEST_BLOB != CANDIDATE_MANIFEST_BLOB:
        raise ValueError("MI01_553_NEW_MANIFEST_HOLD")
    return w8


if __name__ == "__main__":
    try:
        load_candidate().main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print("HOLD:", exc, file=sys.stderr)
        raise SystemExit(1) from exc
