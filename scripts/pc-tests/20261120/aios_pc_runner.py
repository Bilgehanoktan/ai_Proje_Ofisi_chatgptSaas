#!/usr/bin/env python3
"""AI Company OS — pinned disposable PC test launcher (no live grants or acceptance).

Modes:
  allsafe: separate G7 originals + W8 audit/C04 prepare + read-only PG loopback probe
  w8full: ONLY after C05 owner review, with --approved-review-sha and --chromium
Run on the user's Windows PC, not inside ChatGPT's isolated Linux container.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from hashlib import sha1, sha256
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

REPO = "https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas.git"
CANON = "254e0188998d0d245bd8ee4eb901aead02951a66"
W8 = "99571c2e4341d4abd9c9e7b6a6b713ebf7fd9542"
G7 = "93e6c84db1a061ee914aa2c1d543620404515c0b"
PIN = {
    "product/SOURCE_MANIFEST.json": "27b4eb5816265d4e6e6d2458acb6220db7dd0c76",
    "tests/integration/w8_unified_u3.py": "b4043035e75c5a18b7b19a9f18eecfef8e8fe677",
    "tests/integration/w8_frozen_npm.py": "257ba8f110508ff30ad03212111cfe8e2299d801",
}
G7_RUNNER_SHA256 = "da4a644f3d6f189ac6a94fc8a645acde40df6489199f6a702aedf7f87a29a691"


def blob(data: bytes) -> str:
    return sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def must_equal(file: Path, expected: str, algorithm="git") -> None:
    if file.is_symlink() or not file.is_file():
        raise RuntimeError(f"MISSING_OR_LINK_HOLD: {file}")
    data = file.read_bytes()
    actual = blob(data) if algorithm == "git" else sha256(data).hexdigest()
    if actual != expected:
        raise RuntimeError(f"SOURCE_PIN_HOLD: {file}: {actual}, expected {expected}")


class Session:
    def __init__(self, root: Path):
        self.root = root.expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.logs = self.root / "logs"
        self.logs.mkdir(exist_ok=True)
        self.w8_dir = self.root / "checkout_w8_owner_553"
        self.g7_dir = self.root / "checkout_g7_original_562"
        self.w8_stage = self.root / "stage_w8_553"
        self.status = {
            "date": datetime.now(timezone.utc).isoformat(),
            "classification": "LOCAL_DISPOSABLE_TESTS_NOT_RELEASE_OR_SECURITY_ACCEPTANCE",
            "canonical_sha": CANON,
            "W8_AUDIT": "NOT_RUN", "W8_C04": "NOT_RUN", "W8_C05": "HOLD_OWNER_REVIEW",
            "W8_C06": "NOT_RUN", "W8_C07": "NOT_RUN", "W8_C08": "NOT_RUN",
            "G7_CURRENT_ORG_7": "NOT_RUN", "POSTGRES_LOOPBACK": "NOT_RUN",
            "POSTGRES_PROTECTED_RLS_RESTORE": "HOLD", "AUTHORITY_ROOT_SINK": "HOLD",
            "INDEPENDENT_SECURITY_IV": "HOLD", "MVP_ACCEPTANCE": "HOLD_0_OF_11",
            "logs": [], "errors": [],
        }

    def run(self, name: str, args: list[str], cwd: Path | None = None, timeout=None) -> str:
        args = [str(x) for x in args]
        p_out = self.logs / (name + ".stdout.log")
        p_err = self.logs / (name + ".stderr.log")
        print(f"RUN {name}: " + " ".join(args[:3]), flush=True)
        with p_out.open("wb") as out, p_err.open("wb") as err:
            completed = subprocess.run(args, cwd=cwd, stdout=out, stderr=err, timeout=timeout, check=False)
        self.status["logs"].append({"name": name, "stdout": str(p_out), "stderr": str(p_err), "exit": completed.returncode})
        for path in (p_out, p_err):
            if path.stat().st_size:
                print(f"  {path.name} tail:")
                print("\n".join(path.read_text(encoding="utf-8", errors="replace").splitlines()[-12:]))
        if completed.returncode:
            raise RuntimeError(f"RUN_FAILED {name} exit={completed.returncode}; inspect {p_err}")
        return p_out.read_text(encoding="utf-8", errors="replace")

    def checkout(self, target: Path, commit: str, name: str) -> None:
        if not (target / ".git").is_dir():
            if target.exists():
                raise RuntimeError(f"NON_GIT_EXISTING_DIR_HOLD: {target}")
            self.run(name + "_clone", ["git", "-c", "core.longpaths=true", "-c", "core.autocrlf=false", "clone", "--filter=blob:none", "--no-checkout", REPO, str(target)])
        self.run(name + "_autocrlf", ["git", "-C", str(target), "config", "core.autocrlf", "false"])
        self.run(name + "_longpaths", ["git", "-C", str(target), "config", "core.longpaths", "true"])
        self.run(name + "_fetch", ["git", "-C", str(target), "fetch", "--no-tags", "origin", commit])
        self.run(name + "_checkout", ["git", "-C", str(target), "checkout", "--detach", commit])
        head = self.run(name + "_head", ["git", "-C", str(target), "rev-parse", "HEAD"]).strip()
        if head != commit:
            raise RuntimeError(f"CHECKOUT_SHA_HOLD: expected {commit}, got {head}")
        dirty = self.run(name + "_status", ["git", "-C", str(target), "status", "--porcelain", "--untracked-files=all"])
        if dirty.strip():
            raise RuntimeError(f"DIRTY_CHECKOUT_HOLD: {target}: {dirty[:200]}")
        print(f"{name} exact clean SHA OK: {head}")

    def g7(self):
        self.checkout(self.g7_dir, G7, "G7")
        runner = Path(__file__).with_name("verify_current_org_g7.py")
        must_equal(runner, G7_RUNNER_SHA256, "sha256")
        self.run("G7_original_7", [sys.executable, "-B", str(runner), "--root", str(self.g7_dir), "--json-out", str(self.root / "G7_RESULT.json")])
        result = json.loads((self.root / "G7_RESULT.json").read_text(encoding="utf-8"))
        if result.get("tests_executed") != 7 or result.get("tests_passed") != 7:
            raise RuntimeError("G7_ORIGINAL_RESULTS_HOLD")
        self.status["G7_CURRENT_ORG_7"] = "PASS_7_OF_7_SYNTHETIC_D0_CURRENT_PRODUCT_ORG"

    def w8_audit(self) -> Path:
        self.checkout(self.w8_dir, W8, "W8")
        for name, expected in PIN.items():
            must_equal(self.w8_dir / name, expected)
        runner = self.w8_dir / "tests/integration/w8_unified_u3.py"
        self.run("W8_AUDIT", [sys.executable, "-B", str(runner), "audit", "--repo", str(self.w8_dir)])
        self.status["W8_AUDIT"] = "PASS_SOURCE_AUDIT_ONLY"
        return runner

    def w8_prepare(self, runner: Path):
        if self.w8_stage.exists():
            raise RuntimeError(f"C04_STAGE_ALREADY_EXISTS_HOLD: {self.w8_stage}; do not overwrite prior data")
        self.run("W8_C04_PREPARE", [sys.executable, "-B", str(runner), "prepare", "--repo", str(self.w8_dir), "--stage", str(self.w8_stage)])
        review = self.w8_stage / "locks/REVIEW.json"
        if not review.is_file():
            raise RuntimeError("W8_REVIEW_JSON_MISSING_HOLD")
        digest = sha256(review.read_bytes()).hexdigest()
        (self.root / "W8_REVIEW_SHA256_NEEDS_OWNER_APPROVAL.txt").write_text(digest + "\n", encoding="utf-8")
        self.status["W8_C04"] = "PASS_PREPARED_NEEDS_C05_OWNER_PROVENANCE_REVIEW"
        self.status["W8_review_sha256_unapproved"] = digest

    def w8_full(self, approved: str, chromium: Path):
        runner = self.w8_audit()
        approved = approved.lower()
        if not re.fullmatch(r"[a-fA-F0-9]{64}", approved):
            raise RuntimeError("C05_OWNER_APPROVED_REVIEW_SHA256_REQUIRED_NO_SELF_APPROVAL")
        must_equal(self.w8_stage / "locks/REVIEW.json", approved.lower(), "sha256")
        self.status["W8_C05"] = "REVIEW_HASH_MATCH_ONLY_OWNER_APPROVAL_MUST_BE_INDEPENDENT"
        self.run("W8_C06_INSTALL", [sys.executable, "-B", str(runner), "install", "--stage", str(self.w8_stage), "--approve", approved])
        self.status["W8_C06"] = "PASS_LOCAL_ONLY"
        self.run("W8_C07_TEST_BUILD", [sys.executable, "-B", str(runner), "test", "--stage", str(self.w8_stage), "--approve", approved])
        self.status["W8_C07"] = "PASS_LOCAL_ONLY"
        if not chromium.is_file():
            raise RuntimeError("REVIEWED_CHROMIUM_EXECUTABLE_MISSING_HOLD")
        self.run("W8_C08_CHROMIUM", [sys.executable, "-B", str(runner), "smoke", "--stage", str(self.w8_stage), "--approve", approved, "--chromium", str(chromium)])
        self.status["W8_C08"] = "PASS_LOCAL_ONLY_PENDING_OWNER_ACCEPTANCE"

    def pg_probe(self):
        if shutil.which("pg_isready") is None:
            self.status["POSTGRES_LOOPBACK"] = "HOLD_PG_ISREADY_NOT_INSTALLED_OR_NOT_ON_PATH"
            return
        try:
            self.run("PG_LOCAL_READINESS_ONLY", ["pg_isready", "-h", "127.0.0.1", "-p", "5432", "-t", "3"], timeout=8)
            self.status["POSTGRES_LOOPBACK"] = "READY_LOCAL_SOCKET_ONLY_NOT_RLS_OR_RESTORE"
        except Exception as exc:
            self.status["POSTGRES_LOOPBACK"] = "NO_LOCAL_SERVER_ON_127_0_0_1_5432"
            self.status["errors"].append("Postgres read-only probe: " + str(exc))

    def save(self):
        self.status["finished_at"] = datetime.now(timezone.utc).isoformat()
        path = self.root / "PC_TEST_RESULTS.json"
        path.write_text(json.dumps(self.status, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print("Results:", path)
        return path


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mode", choices=("allsafe", "g7", "w8audit", "w8prepare", "w8full", "pgprobe"), default="allsafe")
    p.add_argument("--root", type=Path, default=Path.home() / "AIOS_VERIFY_20261120")
    p.add_argument("--approved-review-sha", default="", help="C05 owner-reviewed SHA256; do not auto-approve")
    p.add_argument("--chromium", type=Path, default=Path("REVIEWED_CHROME_PATH_REQUIRED"))
    a = p.parse_args(argv)
    s = Session(a.root)
    issues = []
    def attempt(label, fn):
        try:
            fn()
        except Exception as exc:
            issues.append(label + ": " + str(exc))
            print("HOLD:", issues[-1], file=sys.stderr)
            s.status["errors"].append(issues[-1])
            gates = {
                "G7_ORIGINAL": ("G7_CURRENT_ORG_7",),
                "W8_PREPARE": ("W8_AUDIT", "W8_C04"),
                "W8_INSTALL_TEST_BROWSER": ("W8_C06", "W8_C07", "W8_C08"),
                "PG_READ_ONLY": ("POSTGRES_LOOPBACK",),
            }
            for gate in gates.get(label, ()):
                if s.status[gate] == "NOT_RUN":
                    s.status[gate] = "ATTEMPT_FAILED_OR_HELD"
    try:
        for tool in ("git", "node", "npm"):
            if shutil.which(tool) is None:
                raise RuntimeError(f"REQUIRED_TOOL_MISSING: {tool}")
        s.run("PYTHON_VERSION", [sys.executable, "--version"])
        s.run("GIT_VERSION", ["git", "--version"])
        s.run("NODE_VERSION", ["node", "--version"])
        s.run("NPM_VERSION", ["npm", "--version"])
        if a.mode in ("allsafe", "g7"):
            attempt("G7_ORIGINAL", s.g7)
        if a.mode in ("allsafe", "w8audit", "w8prepare"):
            def work():
                runner = s.w8_audit()
                if a.mode in ("allsafe", "w8prepare"):
                    s.w8_prepare(runner)
            attempt("W8_PREPARE", work)
        if a.mode == "w8full":
            attempt("W8_INSTALL_TEST_BROWSER", lambda: s.w8_full(a.approved_review_sha, a.chromium))
        if a.mode in ("allsafe", "pgprobe"):
            attempt("PG_READ_ONLY", s.pg_probe)
    except Exception as exc:
        issues.append("ENVIRONMENT: " + str(exc))
        s.status["errors"].append(issues[-1])
    finally:
        s.save()
    if issues:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
