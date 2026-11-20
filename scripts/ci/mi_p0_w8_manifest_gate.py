"""Read-only, fail-closed W8/owner-manifest promotion preflight.

This is not an original W8 install/build/test/browser runner, a security
attestation, or an authorization to repin an owner source. No files are edited.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
from pathlib import Path
import sys


class GateHold(Exception):
    """The candidate is not eligible for W8 manifest promotion."""


def git_blob(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    obj = {}
    for key, value in pairs:
        if key in obj:
            raise GateHold("DUPLICATE_JSON_KEY_HOLD:" + key)
        obj[key] = value
    return obj


def _files(data: bytes) -> dict:
    try:
        root = json.loads(data.decode("utf-8"), object_pairs_hook=_unique_object)
    except (UnicodeError, json.JSONDecodeError, TypeError, ValueError) as exc:
        raise GateHold("INVALID_MANIFEST_HOLD") from exc
    if not isinstance(root, dict) or not isinstance(root.get("files"), dict):
        raise GateHold("MANIFEST_FILES_HOLD")
    files = root["files"]
    if not files:
        raise GateHold("EMPTY_MANIFEST_HOLD")
    for path, metadata in files.items():
        if not isinstance(path, str) or not path or path.startswith("/") or "\\" in path or any(part in ("", ".", "..") for part in path.split("/")):
            raise GateHold("INVALID_MANIFEST_PATH_HOLD")
        if (not isinstance(metadata, dict) or type(metadata.get("bytes")) is not int or metadata["bytes"] < 0
                or not isinstance(metadata.get("sha256"), str) or len(metadata["sha256"]) != 64
                or any(ch not in "0123456789abcdef" for ch in metadata["sha256"])):
            raise GateHold("INVALID_MANIFEST_ENTRY_HOLD:" + path)
    return files


def _w8_pin_and_guard(source: bytes) -> str:
    try:
        tree = ast.parse(source.decode("utf-8"))
    except (SyntaxError, UnicodeError) as exc:
        raise GateHold("INVALID_W8_ADAPTER_HOLD") from exc
    assignments = [node for node in tree.body if isinstance(node, ast.Assign)
                   and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                   and node.targets[0].id == "MANIFEST"]
    if len(assignments) != 1 or not isinstance(assignments[0].value, ast.Constant) or not isinstance(assignments[0].value.value, str):
        raise GateHold("W8_PIN_DECLARATION_HOLD")
    pin = assignments[0].value.value
    if len(pin) != 40 or any(ch not in "0123456789abcdef" for ch in pin):
        raise GateHold("W8_PIN_FORMAT_HOLD")
    funcs = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "extend"]
    if len(funcs) != 1 or not funcs[0].body or not isinstance(funcs[0].body[0], ast.If):
        raise GateHold("W8_GUARD_ORDER_HOLD")
    guard = funcs[0].body[0]
    expected = ast.parse("w.MANIFEST_BLOB != MANIFEST", mode="eval").body
    if ast.dump(guard.test) != ast.dump(expected):
        raise GateHold("W8_GUARD_CONDITION_HOLD")
    if (len(guard.body) != 1 or not isinstance(guard.body[0], ast.Raise)
            or not isinstance(guard.body[0].exc, ast.Call)
            or not isinstance(guard.body[0].exc.func, ast.Name)
            or guard.body[0].exc.func.id != "ValueError"
            or len(guard.body[0].exc.args) != 1
            or not isinstance(guard.body[0].exc.args[0], ast.Constant)
            or guard.body[0].exc.args[0].value != "U3_MANIFEST_HOLD"):
        raise GateHold("W8_FAIL_CLOSED_HOLD")
    return pin


def assess(canonical: bytes, candidate: bytes, adapter: bytes, *,
           canonical_blob: str, candidate_blob: str, adapter_blob: str) -> dict:
    """Prove expected input blob pins and W8 guard; return HOLD for mismatch."""
    blobs = {"canonical": git_blob(canonical), "candidate": git_blob(candidate), "adapter": git_blob(adapter)}
    expected = {"canonical": canonical_blob, "candidate": candidate_blob, "adapter": adapter_blob}
    if blobs != expected:
        raise GateHold("INPUT_GIT_BLOB_HOLD:" + ",".join(k for k in blobs if blobs[k] != expected[k]))
    old, new = _files(canonical), _files(candidate)
    pin = _w8_pin_and_guard(adapter)
    added = sorted(set(new) - set(old))
    removed = sorted(set(old) - set(new))
    changed = sorted(k for k in old.keys() & new.keys() if old[k] != new[k])
    result = {"status": "HOLD" if candidate_blob != pin else "MANIFEST_PRECHECK_MATCH_ONLY",
              "gate": "U3_MANIFEST_HOLD" if candidate_blob != pin else "NONE_FOR_MANIFEST_ONLY",
              "canonical_manifest_blob": canonical_blob,
              "candidate_manifest_blob": candidate_blob,
              "w8_adapter_blob": adapter_blob,
              "w8_adapter_manifest_pin": pin,
              "canonical_entries": len(old), "candidate_entries": len(new),
              "added": added, "removed": removed, "changed": changed,
              "original_w8_build": "NOT_RUN", "product_acceptance": "HOLD",
              "independent_security_acceptance": "HOLD",
              "next": "Owner-reviewed exact repin and original W8 chain only after source/security approvals"}
    if pin != canonical_blob:
        result["status"] = "HOLD"
        result["gate"] = "W8_BASE_PIN_MISMATCH_HOLD"
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--canonical", type=Path, required=True)
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--adapter", type=Path, required=True)
    p.add_argument("--canonical-blob", required=True)
    p.add_argument("--candidate-blob", required=True)
    p.add_argument("--adapter-blob", required=True)
    args = p.parse_args(argv)
    try:
        result = assess(args.canonical.read_bytes(), args.candidate.read_bytes(), args.adapter.read_bytes(),
                        canonical_blob=args.canonical_blob, candidate_blob=args.candidate_blob,
                        adapter_blob=args.adapter_blob)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 2 if result["status"] == "HOLD" else 0
    except (GateHold, OSError) as exc:
        print(json.dumps({"status": "HOLD", "reason": str(exc), "original_w8_build": "NOT_RUN",
                          "product_acceptance": "HOLD"}, ensure_ascii=False, sort_keys=True))
        return 2


if __name__ == "__main__":
    sys.exit(main())
