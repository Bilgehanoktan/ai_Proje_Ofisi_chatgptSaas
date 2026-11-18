import os
import sys
import json
import hashlib
import shutil
import subprocess
from pathlib import Path

root = Path(r"C:\AICOS\R8-9675d4e1")
stage = Path(r"C:\AICOS\R8-frontend-stage")
front = stage / "frontend"

if not __debug__:
    raise RuntimeError("Run without Python -O")

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

review_pin = "6561fbaded150cd32b2d1fe8c01f1d500bc8486ae3415b632464d18d2c7dbe4c"
lock_pin = "036fd649daf67874646018c12de91b6e27bb38acc3a0aef2989f7b67aad06c88"

review = json.loads((stage / "REVIEW.json").read_bytes())

def verify_pins():
    assert sha(stage / "REVIEW.json") == review_pin
    assert sha(front / "package-lock.json") == lock_pin
    assert sha(stage / "npm-audit.json") == review["audit_sha256"]

verify_pins()

manifest = root / "product/SOURCE_MANIFEST.json"
raw = manifest.read_bytes()

assert hashlib.sha1(
    b"blob " + str(len(raw)).encode() + b"\0" + raw
).hexdigest() == review["source_manifest"]

prefix = "ai-company-os-frontend/"

files = {
    name[len(prefix):]: info
    for name, info in json.loads(raw)["files"].items()
    if name.startswith(prefix)
}

assert len(files) == 265

def verify_sources():
    for name, info in files.items():
        p = front / name
        assert p.is_file(), name
        assert not p.is_symlink(), name
        assert p.resolve() == p.absolute(), name
        assert p.stat().st_size == info["bytes"], name
        assert sha(p) == info["sha256"], name

verify_sources()

actual = {
    p.relative_to(front).as_posix()
    for p in front.rglob("*") if p.is_file()
}

assert actual == set(files) | {"package-lock.json"}
assert not (front / "node_modules").exists()
assert not (front / ".next").exists()

print("FRONTEND SOURCE: 265/265 PASS", flush=True)

node = Path(shutil.which("node"))
npm = node.parent / "node_modules/npm/bin/npm-cli.js"

assert npm.is_file(), "npm CLI not found"

allowed = {
    "PATH", "SYSTEMROOT", "WINDIR", "COMSPEC",
    "PATHEXT", "TEMP", "TMP", "HOME",
    "USERPROFILE", "LOCALAPPDATA", "APPDATA",
    "SYSTEMDRIVE", "HOMEDRIVE", "HOMEPATH",
    "NUMBER_OF_PROCESSORS", "PROCESSOR_ARCHITECTURE"
}

env = {k:v for k,v in os.environ.items() if k.upper() in allowed}

# Preserve the original failed attempt's empty.npmrc as evidence.
# npm rejects the same file being loaded as both user and global config.
user_config = stage / "r8-user.npmrc"
global_config = stage / "r8-global.npmrc"
assert user_config != global_config
for p in (user_config, global_config):
    assert not p.exists(), f"Configuration path already exists: {p}"
for label in ("01-npm-install", "02-next-build", "03-typecheck"):
    assert not (stage / (label + ".log")).exists(), label
for p in (user_config, global_config):
    p.touch(exist_ok=False)

env.update(
    NEXT_TELEMETRY_DISABLED="1",
    NO_PROXY="127.0.0.1,localhost",
    NPM_CONFIG_USERCONFIG=str(user_config),
    NPM_CONFIG_GLOBALCONFIG=str(global_config),
    NPM_CONFIG_CACHE=str(stage / "npm-cache"),
    NPM_CONFIG_REGISTRY="https://registry.npmjs.org"
)

def run(label, args):
    logfile = stage / (label + ".log")
    print("===", label, "===", flush=True)

    with logfile.open("xb") as log:
        with subprocess.Popen(
            [str(x) for x in args],
            cwd=front,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        ) as proc:
            for line in proc.stdout:
                log.write(line)
                log.flush()
                print(line.decode("utf-8", errors="replace").rstrip(), flush=True)

            code = proc.wait()

    print(label, "EXIT CODE:", code)
    print(label, "SHA256:", sha(logfile))

    verify_pins()

    if code != 0:
        sys.exit(code)

assert subprocess.check_output(
    [str(node), "--version"], env=env, text=True
).strip() == "v24.14.0"

assert subprocess.check_output(
    [str(node), str(npm), "--version"], cwd=front, env=env, text=True
).strip() == "11.9.0"

print("NPM CONFIG SEPARATION: PASS", flush=True)

run("01-npm-install", [
    node, npm, "ci",
    "--ignore-scripts",
    "--include=dev",
    "--include=optional",
    "--no-audit",
    "--no-fund",
    "--strict-ssl=true",
    "--registry=https://registry.npmjs.org"
])

verify_sources()

print("LOCKED INSTALL: PASS", flush=True)

run("02-next-build", [
    node,
    front / "node_modules/next/dist/bin/next",
    "build"
])

run("03-typecheck", [
    node,
    front / "node_modules/typescript/bin/tsc",
    "--noEmit"
])

verify_pins()
verify_sources()

print("ORIGINAL FRONTEND SOURCES: PRESERVED")
print("ORIGINAL LOCK: PRESERVED")
print("R8 FRONTEND BUILD: PASS")
