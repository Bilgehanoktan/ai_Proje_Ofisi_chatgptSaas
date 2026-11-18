"""Run only MEM-05C diagnostics against exact pinned sources in a temporary directory."""
from hashlib import sha1
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile

HERE=Path(__file__).resolve().parent

def main():
    root=Path(subprocess.check_output(["git","-C",str(HERE),"rev-parse","--show-toplevel"],text=True).strip())
    pins=json.loads((HERE/"SOURCE_PINS.json").read_text(encoding="utf-8"))["files"]
    with tempfile.TemporaryDirectory(prefix="mem05c-") as tmp:
        stage=Path(tmp)
        seen=set()
        for item in pins:
            path=item["path"]
            dest=(stage/path).resolve()
            if not dest.is_relative_to(stage) or path in seen:
                raise ValueError("PIN_PATH_HOLD")
            seen.add(path)
            raw=subprocess.check_output(["git","-C",str(root),"show",item["ref"]+":"+path])
            blob=sha1(b"blob "+str(len(raw)).encode("ascii")+b"\0"+raw).hexdigest()
            if blob!=item["blob"]:
                raise ValueError("SOURCE_BLOB_MISMATCH: "+path)
            dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(raw)
        test=stage/"test_memory_gateway.py"
        test.write_bytes((HERE/"test_memory_gateway.py").read_bytes())
        backend=stage/"product"/"ai-company-os-backend"
        env=os.environ.copy()
        env["PYTHONPATH"]=os.pathsep.join(map(str,(backend,backend/"tests",stage/"tests"/"w5")))
        print("SOURCE_PINS_VERIFIED="+str(len(pins)),flush=True)
        return subprocess.call([sys.executable,"-B",str(test)],cwd=stage,env=env)

if __name__=="__main__":
    try:
        sys.exit(main())
    except (OSError,ValueError,subprocess.CalledProcessError) as exc:
        print("BLOCKED: "+str(exc),file=sys.stderr)
        sys.exit(2)
