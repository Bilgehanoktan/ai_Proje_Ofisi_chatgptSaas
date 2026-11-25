"""Diagnostic only: run the exact plan endpoint AST, not the full product ASGI app."""
import ast, hashlib, json
from pathlib import Path
from hashlib import sha256
from fastapi import FastAPI
from app.core.orchestrator.engine import canonical_plan
from app.core.task_engine.dag import GraphError
source=Path(__file__).parent/'app/api/demo.py'
raw=source.read_bytes()
assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()=='32a1bac1336dfd9ed625d74a59c01cb92baf303a'
app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
FIXTURE=Path(__file__).parent/'fixtures/office.snapshot.json'
nodes=[n for n in ast.parse(raw).body if (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_CORE_PLAN_FILES' for t in n.targets)) or (isinstance(n,ast.FunctionDef) and n.name in {'_pinned_plan_json','_canonical_plan_wire','plan_projection'})]
assert len(nodes)==4
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),globals())
