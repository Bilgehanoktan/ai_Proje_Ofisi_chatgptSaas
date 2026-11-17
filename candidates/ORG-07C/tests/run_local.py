"""Compile selected exact product transport and run local HTTP tests. No install/CI."""
from pathlib import Path
import os, subprocess, sys, tempfile, json, time, urllib.request, hashlib
HERE=Path(__file__).resolve().parents[1]
subprocess.run([sys.executable,'-B',str(HERE/'make_product_patch.py')],check=True)
with tempfile.TemporaryDirectory() as tmp:
 staged=HERE/'staged'; js=Path(tmp)/'js'
 subprocess.run(['tsc','--strict','--target','ES2022','--module','commonjs','--lib','ES2022,DOM','--rootDir','features','--outDir',str(js),'features/organization/organizationProjection.ts','features/organization/organizationProxy.ts','features/data/projectionRead.ts'],cwd=staged,check=True)
 p=subprocess.Popen([sys.executable,'-B',str(HERE/'tests/loopback_fixture.py')],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 try:
  info=json.loads(p.stdout.readline()); port=info['port']
  for i in range(50):
   try:
    with urllib.request.urlopen(f'http://127.0.0.1:{port}/test-only/integrity',timeout=.2) as r: assert json.load(r)['unchanged']
    break
   except OSError: time.sleep(.1)
  else: raise RuntimeError('FIXTURE_NOT_READY')
  env={**os.environ,'ORG07C_JS':str(js),'ORG07C_PORT':str(port),'ORG07C_HEAD':info['head']}
  result=subprocess.run(['node','--test',str(HERE/'tests/organization.test.cjs')],env=env,capture_output=True,text=True,timeout=60)
  (HERE/'test.log').write_text(result.stdout+result.stderr);print(result.stdout);sys.exit(result.returncode)
 finally:
  p.terminate()
  try:p.wait(timeout=5)
  except subprocess.TimeoutExpired:p.kill();p.wait()
