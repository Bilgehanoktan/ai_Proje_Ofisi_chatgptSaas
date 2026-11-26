"""Start an owner-reviewed isolated R6 frontend/backend pair; no tests or installs.

This is process composition, NOT a security approval verifier, agent dispatcher,
or a way to start the archived HOLD source. Use only a prepared DEV checkout
and interpreter/build already cleared by their respective source/dependency owners.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import signal
import stat
import subprocess
import sys
import time


def fail(message):
    raise SystemExit("HOLD: " + message)


def regular(path):
    if path.is_symlink() or not path.is_file():
        fail("missing or non-regular file: " + str(path))
    st = path.lstat()
    if getattr(st, "st_file_attributes", 0) & 0x400:
        fail("reparse point: " + str(path))
    if not stat.S_ISREG(st.st_mode):
        fail("not a regular file: " + str(path))
    return path


def pinned_path(root, rel):
    parts = PurePosixPath(rel).parts
    if (not parts or PurePosixPath(rel).is_absolute() or
            any(p in ("", ".", "..") or ":" in p or "\\" in p for p in rel.split("/"))):
        fail("invalid manifest path")
    path = root
    for part in parts:
        path = path / part
        if path.is_symlink() or (path.exists() and getattr(path.lstat(), "st_file_attributes", 0) & 0x400):
            fail("linked manifest path: " + rel)
    return regular(path)


def verify_source(root, expected_blob):
    manifest = pinned_path(root, "product/SOURCE_MANIFEST.json")
    raw = manifest.read_bytes()
    actual = hashlib.sha1(("blob %d\0" % len(raw)).encode("ascii") + raw).hexdigest()
    if actual != expected_blob:
        fail("manifest Git blob mismatch")
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                fail("duplicate manifest key")
            obj[key] = value
        return obj
    data = json.loads(raw, object_pairs_hook=unique)
    status = data.get("status")
    if not isinstance(status, str) or not status.strip():
        fail("manifest status missing")
    upper = status.upper()
    if any(word in upper for word in ("HOLD", "NOT_EXECUTION_APPROVED", "REVIEW_ONLY", "QUARANTINE", "DENY", "ARCHIVAL")):
        fail("source manifest is restricted: " + status)
    # Non-restricted metadata and matching bytes do not prove owner approval.
    # Approval must already exist outside this launcher; no flag grants it.
    files = data.get("files")
    if not isinstance(files, dict) or not files:
        fail("manifest inventory missing")
    seen = set()
    for rel, meta in files.items():
        if rel.casefold() in seen:
            fail("case-alias manifest path")
        seen.add(rel.casefold())
        path = pinned_path(root / "product", rel)
        content = path.read_bytes()
        if (not isinstance(meta, dict) or type(meta.get("bytes")) is not int
                or len(content) != meta["bytes"]
                or hashlib.sha256(content).hexdigest() != meta.get("sha256")):
            fail("source bytes mismatch: " + rel)
    for rel in ("ai-company-os-backend/app/main.py",
                "ai-company-os-frontend/features/mvp/localBackend.ts",
                "ai-company-os-frontend/package.json",
                "ai-company-os-frontend/package-lock.json"):
        if rel not in files:
            fail("required entry absent from manifest: " + rel)


def local_port(value):
    if not 1024 <= value <= 49151:
        fail("port outside supported local range")
    return value


def clean_env():
    # Do not pass API keys, database URLs, PYTHONPATH, NODE_OPTIONS, or proxies.
    keys = {"PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TEMP", "TMP",
            "TMPDIR", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "HOME", "LANG",
            "LC_ALL", "TZ", "SYSTEMDRIVE", "PROGRAMDATA", "HOMEDRIVE", "HOMEPATH"}
    env = {k: v for k, v in os.environ.items() if k.upper() in keys}
    env["NEXT_TELEMETRY_DISABLED"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def stop(children):
    for child in reversed(children):
        if child.poll() is None:
            try:
                if os.name == "posix":
                    os.killpg(child.pid, signal.SIGTERM)
                else:
                    child.terminate()
            except ProcessLookupError:
                pass
    for child in reversed(children):
        try:
            child.wait(timeout=8)
        except subprocess.TimeoutExpired:
            try:
                if os.name == "posix":
                    os.killpg(child.pid, signal.SIGKILL)
                else:
                    child.kill()
            except ProcessLookupError:
                pass
            child.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path, help="prepared isolated checkout")
    parser.add_argument("--manifest-blob", required=True, help="independently pinned DEV manifest Git blob")
    parser.add_argument("--python", required=True, type=Path, help="reviewed backend venv executable")
    parser.add_argument("--node", required=True, type=Path, help="reviewed Node executable")
    parser.add_argument("--backend-port", type=int, default=8000)
    parser.add_argument("--frontend-port", type=int, default=3000)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9a-f]{40}", args.manifest_blob):
        fail("manifest blob must be a lowercase Git SHA")
    root = args.root.resolve(strict=True)
    verify_source(root, args.manifest_blob)
    backend = root / "product" / "ai-company-os-backend"
    frontend = root / "product" / "ai-company-os-frontend"
    for folder in (backend, frontend):
        for item in folder.glob(".env*"):
            if item.name != ".env.example":
                fail("local environment file not allowed for this D0 launcher: " + str(item))
    if not args.python.is_absolute() or not args.node.is_absolute():
        fail("absolute reviewed executable paths required")
    python = regular(args.python)
    node = regular(args.node)
    next_cli = regular(frontend / "node_modules" / "next" / "dist" / "bin" / "next")
    regular(frontend / ".next" / "BUILD_ID")
    backend_port, frontend_port = map(local_port, (args.backend_port, args.frontend_port))
    if backend_port == frontend_port:
        fail("backend and frontend require different ports")
    env = clean_env()
    env["AICOS_D0_BACKEND_PORT"] = str(backend_port)
    env["NODE_ENV"] = "production"
    commands = [
        ([str(python), "-I", "-B", "-m", "uvicorn", "app.main:app",
          "--app-dir", str(backend), "--host", "127.0.0.1", "--port", str(backend_port)], backend),
        ([str(node), str(next_cli), "start", "-H", "127.0.0.1", "-p", str(frontend_port)], frontend),
    ]
    children = []
    try:
        for command, cwd in commands:
            children.append(subprocess.Popen(command, cwd=cwd, env=env,
                            start_new_session=(os.name == "posix")))
        print("Processes started; readiness and agent execution are not established.", flush=True)
        print("CEO UI: http://127.0.0.1:%d/" % frontend_port, flush=True)
        print("Backend: http://127.0.0.1:%d/demo/v1/status" % backend_port, flush=True)
        print("Ctrl+C stops both processes. No provider/worker is activated by this launcher.", flush=True)
        while True:
            for child in children:
                result = child.poll()
                if result is not None:
                    print("Process exited: %d; stopping the paired session." % result, file=sys.stderr)
                    return result if result else 1
            time.sleep(0.5)
    except KeyboardInterrupt:
        return 130
    finally:
        stop(children)


if __name__ == "__main__":
    sys.exit(main())
