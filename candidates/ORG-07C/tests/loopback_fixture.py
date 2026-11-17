"""Disposable R3 database + real Uvicorn, only for local ORG-07C tests."""
from pathlib import Path
from dataclasses import replace
import hashlib, json, socket, sys
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
ROOT=Path(__file__).resolve().parents[2]; A=ROOT/'ORG-07A'; R3=ROOT/'ORG-05R3'
sys.path[:0]=[str(A),str(R3)]
from test_studio_original import PINS
for n,h in {**{str(R3/k):v for k,v in PINS.items()},str(A/'studio_router.py'):'eda507f8e5933c27568064455eccc4cf85bbba0c',str(A/'test_studio_original.py'):'b928799ddc46fb0f49ee2b6e05199fa173777813'}.items():
 raw=Path(n).read_bytes();assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==h,n
from test_durable_ops import DurableTests
from durable_ops import ReadSession
from studio_router import build_router, ServerReadContext
f=DurableTests();f.setUp()
try:
 before=hashlib.sha256(f.path.read_bytes()).hexdigest()
 session=ReadSession(f.scope,'demo-reader',100,'org.preview.read')
 def resolve(token):
  if token=='opaque-valid':return session
  if token=='opaque-expired':return replace(session,expires=99)
  if token=='opaque-other':return replace(session,scope=replace(session.scope,tenant='synthetic-other'))
  return None
 app=FastAPI();app.include_router(build_router(lambda:ServerReadContext(f.path,f.rev,resolve,lambda:99),R3/'studio.schema.json'))
 @app.get('/test-only/integrity')
 def integrity():return JSONResponse({'unchanged':hashlib.sha256(f.path.read_bytes()).hexdigest()==before})
 sock=socket.socket();sock.bind(('127.0.0.1',0));sock.listen();port=sock.getsockname()[1]
 if not 1024<=port<=49151:
  sock.close();sock=socket.socket();sock.bind(('127.0.0.1',39027));sock.listen();port=sock.getsockname()[1]
 print(json.dumps({'port':port,'head':f.rev}),flush=True)
 uvicorn.Server(uvicorn.Config(app,log_level='warning',access_log=False)).run(sockets=[sock])
finally:f.doCleanups()
