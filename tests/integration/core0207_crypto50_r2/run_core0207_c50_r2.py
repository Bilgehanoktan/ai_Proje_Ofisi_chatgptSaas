#!/usr/bin/env python3
"""Review-only Core0207-C50-R2 D0 regression (certifi 2026.11.20); NOT original W8 C07.

Runs the same 55 byte-pinned historical files and four exact test modules
against the immutable PR37 C06-installed cryptography 50.0.2 and certifi 2026.11.20 environment.
No historical lock/runner edit, no diagnostic-unpinned flag, no W8 markers.
Owner acceptance and an updated W8 adapter remain separate HOLD decisions.
"""
import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys
import tempfile

CONTRACT_BLOB = "e48c5855d70860cbc35442e1898780839c79b214"


def git_blob(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def exact_file(path, expected_blob=None, expected_sha=None):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(),
            "MISSING_OR_SYMLINK_FILE: " + str(path))
    data = path.read_bytes()
    if expected_blob is not None:
        require(git_blob(data) == expected_blob, "GIT_BLOB_MISMATCH: " + str(path))
    if expected_sha is not None:
        require(hashlib.sha256(data).hexdigest() == expected_sha,
                "SHA256_MISMATCH: " + str(path))
    return data


def import_pinned(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    require(spec is not None and spec.loader is not None, "MODULE_SPEC_HOLD")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def validate(stage, runner_root, contract):
    require(stage.is_dir() and not stage.is_symlink(), "STAGE_DIRECTORY_HOLD")
    require(runner_root.is_dir() and not runner_root.is_symlink(), "RUNNER_ROOT_HOLD")
    require(sys.version_info[:3] == (3, 13, 17), "PYTHON_3_13_17_REQUIRED")
    require(sqlite3.sqlite_version_info >= (3, 37), "SQLITE_VERSION_HOLD")
    expected_python = stage / ".venv/Scripts/python.exe"
    exact_file(expected_python)
    require(Path(sys.executable).resolve() == expected_python.resolve(),
            "NOT_PR37_APPROVED_VENV_PYTHON")

    review_path = stage / "locks/REVIEW.json"
    manifest_path = stage / "product/SOURCE_MANIFEST.json"
    marker_path = stage / "INSTALL_OK"
    review = json.loads(exact_file(
        review_path, expected_sha=contract["pr37_c04_c06_review_sha256"]
    ))
    exact_file(manifest_path, expected_blob=contract["pr37_stage_manifest_blob"])
    require(review.get("manifest_blob") == contract["pr37_stage_manifest_blob"],
            "PR37_REVIEW_MANIFEST_HOLD")
    require(review.get("python_lock_sha256") == contract["pr37_python_lock_sha256"],
            "PR37_PYTHON_LOCK_PIN_HOLD")
    require(review.get("npm_lock_sha256") == contract["pr37_npm_lock_sha256"],
            "PR37_NPM_LOCK_PIN_HOLD")
    wheels = review.get("wheels", {})
    require(isinstance(wheels, dict) and
            len(wheels) == contract["pr37_expected_wheel_count"],
            "PR37_WHEEL_COUNT_HOLD")
    require(wheels.get(contract["pr37_certifi_wheel_filename"]) ==
            contract["pr37_certifi_wheel_sha256"], "PR37_CERTIFI_GRAPH_HOLD")
    exact_file(stage / "locks/python.lock",
               expected_sha=contract["pr37_python_lock_sha256"])
    exact_file(stage / "product/ai-company-os-frontend/package-lock.json",
               expected_sha=contract["pr37_npm_lock_sha256"])
    exact_file(stage / "locks/wheels" / contract["pr37_certifi_wheel_filename"],
               expected_sha=contract["pr37_certifi_wheel_sha256"])
    marker = exact_file(marker_path).decode("utf-8").strip()
    require(marker == contract["pr37_c04_c06_review_sha256"], "C06_MARKER_HOLD")
    require(not (stage / "BUILD_TEST_OK").exists(), "ORIGINAL_C07_STAGE_MARKER_CHANGED_HOLD")

    original_runner = runner_root / "run_core_0207.py"
    original_helper = runner_root / "run_lifecycle_p05.py"
    original_lock = runner_root / "core_0207_source_lock.json"
    original_p24 = runner_root / "w8_p10j24.py"
    exact_file(original_runner, expected_blob=contract["historical_test_runner_blob"])
    exact_file(original_helper, expected_blob=contract["historical_test_helper_blob"])
    raw = exact_file(original_lock, expected_blob=contract["historical_source_lock_blob"])
    exact_file(original_p24, expected_blob=contract["historical_p24_blob"])

    lock = json.loads(raw)
    require(lock["source_commit"] == contract["historical_source_commit"],
            "HISTORICAL_COMMIT_HOLD")
    require(lock["source_manifest_blob"] == contract["historical_source_manifest_blob"],
            "HISTORICAL_SOURCE_MANIFEST_HOLD")
    require(len(lock["files"]) == contract["historical_file_count"] == 55,
            "HISTORICAL_FILES_COUNT_HOLD")
    require({r["module"]: r["count"] for r in lock["tests"]}
            == contract["module_test_counts"], "HISTORICAL_TEST_MODULES_HOLD")
    require(lock["direct_dependency_pins"]
            == contract["historical_direct_dependency_pins"],
            "HISTORICAL_DIRECT_PINS_CHANGED_HOLD")
    require(contract["historical_direct_dependency_pins"]["cryptography"] == "46.0.4"
            and contract["successor_direct_dependency_pins"]["cryptography"] == "50.0.2",
            "C50_SUCCESSOR_SCOPE_HOLD")
    require(contract["state"] == "OWNER_REVIEW_CANDIDATE_NOT_C07_NOT_C05",
            "CONTRACT_STATE_HOLD")
    return lock, original_helper


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--stage", type=Path, required=True,
                   help="New C06-reviewed PR37 dependency graph stage directory")
    p.add_argument("--runner-root", type=Path, required=True,
                   help="Exact original W8 stage source/tests/integration directory")
    p.add_argument("--source", type=Path, required=True,
                   help="Already reconstructed exact historical 55-file source directory")
    p.add_argument("--report", type=Path, required=True,
                   help="New output JSON path outside original stage")
    args = p.parse_args()
    if args.report.exists() or args.report.is_symlink():
        p.error("report must be a new path")
    if not args.report.parent.is_dir():
        p.error("report parent must exist")
    if args.report.resolve().is_relative_to(args.stage.resolve()):
        p.error("report must be outside original stage")
    if args.report.resolve().is_relative_to(args.runner_root.resolve()):
        p.error("report must not modify original runner source")
    if not args.source.is_dir() or args.source.is_symlink():
        p.error("historical source directory required")
    if args.source.resolve().is_relative_to(args.stage.resolve()):
        p.error("historical source must be separate from original stage")

    result = {
        "contract": "MI01-W8-CORE0207-C50-R2-CERTIFI-20261120",
        "suite_classification": "VERSIONED_LOCAL_D0_CANDIDATE_NOT_W8_C07",
        "acceptance": "OWNER_REVIEW_REQUIRED",
        "W8_C07": "HOLD",
        "W8_C08": "NOT_RUN",
        "independent_C05": "HOLD",
        "status": "HOLD",
        "passed": None,
        "source_files_verified": 0,
    }
    try:
        contract = json.loads(exact_file(
            Path(__file__).with_name("CONTRACT.json"), expected_blob=CONTRACT_BLOB
        ))
        lock, helper_path = validate(args.stage, args.runner_root, contract)
        versions = {}
        for name in contract["successor_direct_dependency_pins"]:
            try:
                versions[name] = importlib.metadata.version(name)
            except importlib.metadata.PackageNotFoundError:
                versions[name] = None
        result["dependency_versions"] = versions
        require(versions == contract["successor_direct_dependency_pins"],
                "VERSIONED_C50_DIRECT_PINS_MISMATCH")
        certifi_version = importlib.metadata.version("certifi")
        require(certifi_version == "2026.11.20", "CERTIFI_2026_11_20_VERSION_HOLD")
        result["certifi_version"] = certifi_version
        helper = import_pinned(helper_path, "core0207_c50_r2_historical_helper")

        with tempfile.TemporaryDirectory(prefix="aios-core0207-c50-r2-") as work:
            isolated = Path(work)
            helper.materialize(args.source, isolated, lock)
            result["source_files_verified"] = len(lock["files"])
            cases = helper.run_cases(isolated, contract["module_test_counts"])
            for item in lock["files"]:
                helper.check_bytes((isolated / item["path"]).read_bytes(), item)
            result.update(cases)

        require(result.get("status") == "PASS" and result.get("passed") == 29,
                "VERSIONED_C50_CASES_NOT_29_OF_29")
        require(result.get("source_files_verified") == 55,
                "SOURCE_55_HOLD")
        result["contract_pin"] = CONTRACT_BLOB
        result["stage_review_sha256"] = contract["pr37_c04_c06_review_sha256"]
        result["original_historical_lock_blob"] = contract["historical_source_lock_blob"]
        # Re-check immutable inputs after running; no test may alter the stage.
        validate(args.stage, args.runner_root, contract)
        result["immutable_stage_guards_preserved"] = True
    except Exception as exc:
        result.update(status="HOLD", passed=None,
                      reason=type(exc).__name__ + ": " + str(exc))
    with args.report.open("x", encoding="utf-8") as out:
        json.dump(result, out, indent=2, ensure_ascii=False)
        out.write("\n")
    print("CORE0207_C50_R2_CANDIDATE:", result["status"],
          "passed=", result["passed"], "W8_C07=HOLD", flush=True)
    print("REPORT:", str(args.report), flush=True)
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
