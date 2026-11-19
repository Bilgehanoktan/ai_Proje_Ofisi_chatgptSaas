"""MI-07/08: exact selected-source common-tree regression. D0 only."""
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PINS = HERE / "COMBINED_PINS.json"
EXPECTED = 344
GROUPS = (
    ("MEM", 184, ("test_memory_gateway_recovery_w5_mem05e", "test_memory_recovery_w5_mem05d", "test_memory_history_w5_mem03", "test_memory_checkpoint_w5_mem04", "test_memory_gateway_05c_r2", "test_memory_gateway_05c_r1", "test_router_cost_review", "test_memory_access_0194", "test_memory_store_0196", "test_runtime_memory_model_0207", "test_joint_context_0208", "test_memory_witness_0209")),
    ("W5-A-F-without-router", 80, ("test_decision_accounting_review", "test_durable_provider_runtime_review", "test_effect_budget_review", "test_invocation_receipt_review", "test_model_profile_review")),
    ("W5-G", 16, ("test_physical_mapping",)),
    ("W5-H", 28, ("test_receipt_pep_review",)),
    ("W5-I", 36, ("test_capability_runtime_review",)),
)
CHILD = """import json,sys,unittest
from pathlib import Path
r=Path.cwd()
b=r/'product/ai-company-os-backend'
group,count,modules=json.loads(sys.argv[1])
paths=[b,b/'tests',r/'tests/w5'] if group=='MEM' else [b,r/'tests/w5',b/'tests']
paths += [r/'candidates/W5-G',r/'candidates/W5-H',r/'candidates/W5-I']
sys.path[:0]=list(map(str,paths))
suite=unittest.defaultTestLoader.loadTestsFromNames(modules)
def flatten(s):
    for x in s:
        if isinstance(x,unittest.TestSuite):
            yield from flatten(x)
        else:
            yield x.id()
ids=list(flatten(suite))
if len(ids)!=count or len(set(ids))!=count:
    print('COLLECTION_HOLD',group,len(ids),len(set(ids)),flush=True)
    sys.exit(2)
result=unittest.TextTestRunner(verbosity=2).run(suite)
print('TEST_IDS_JSON='+json.dumps(ids),flush=True)
counts=[result.testsRun,len(result.failures),len(result.errors),len(result.skipped),len(result.expectedFailures),len(result.unexpectedSuccesses)]
print('GROUP_COUNTS='+json.dumps(counts),flush=True)
sys.exit(0 if result.wasSuccessful() and counts==[count,0,0,0,0,0] else 1)
"""

def verify():
    pins=json.loads(PINS.read_text(encoding="utf-8"))
    if len(pins)!=114:
        raise ValueError("PIN_COUNT_HOLD")
    sources={}
    for rel,pin in sorted(pins.items()):
        p=ROOT/rel
        if not p.is_file() or p.resolve()!=p or not p.is_relative_to(ROOT):
            raise ValueError("SOURCE_PATH_HOLD: "+rel)
        data=p.read_bytes()
        blob=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
        if len(data)!=pin["bytes"] or blob!=pin["blob"] or ("sha256" in pin and hashlib.sha256(data).hexdigest()!=pin["sha256"]):
            raise ValueError("SOURCE_PIN_HOLD: "+rel)
        sources[rel]=data
    print("SOURCE_PINS=114/114",flush=True)
    return sources

def main():
    try:
        sources=verify()
        versions=(sys.version.split()[0],sqlite3.sqlite_version,metadata.version("cryptography"))
        print("ENV="+"/".join(versions),flush=True)
        if versions!=("3.13.5","3.46.1","46.0.4"):
            raise ValueError("REFERENCE_ENVIRONMENT_HOLD")
    except Exception as exc:
        print("BLOCKED: "+str(exc),flush=True)
        return 2
    total=0
    all_ids=set()
    failed=False
    with tempfile.TemporaryDirectory(prefix="mi0708-") as tmp:
        for rel,data in sources.items():
            p=Path(tmp)/rel
            p.parent.mkdir(parents=True,exist_ok=True)
            p.write_bytes(data)
        for group,count,modules in GROUPS:
            print("BEGIN "+group,flush=True)
            result=subprocess.run([sys.executable,"-I","-B","-c",CHILD,json.dumps([group,count,modules])],cwd=tmp,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
            print(result.stdout,end="",flush=True)
            ids=[line[14:] for line in result.stdout.splitlines() if line.startswith("TEST_IDS_JSON=")]
            observed=json.loads(ids[0]) if len(ids)==1 else []
            if result.returncode or len(observed)!=count or len(set(observed))!=count or all_ids.intersection(observed):
                failed=True
                break
            all_ids.update(observed)
            total+=count
        for rel,data in sources.items():
            p=Path(tmp)/rel
            if not p.is_file() or p.read_bytes()!=data:
                print("STAGED_SOURCE_DRIFT="+rel,flush=True)
                failed=True
    try:
        verify()
    except Exception as exc:
        print("POSTCHECK_BLOCKED: "+str(exc),flush=True)
        return 2
    code=int(failed or total!=EXPECTED or len(all_ids)!=EXPECTED)
    print("TOTAL_PASSED_GROUP_TESTS="+str(total),flush=True)
    print("EXIT_CODE="+str(code),flush=True)
    print("PRODUCT_ACCEPTANCE=HOLD",flush=True)
    return code

if __name__=="__main__":
    sys.exit(main())
