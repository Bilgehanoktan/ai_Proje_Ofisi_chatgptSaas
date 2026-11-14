"""Offline packaging of exact GitHub 0160 tree + exact 0159-B parent. No product, Git, CI or network."""
from pathlib import Path, PurePosixPath
import hashlib,json,zipfile,shutil,tempfile,sys,os
HERE=Path(__file__).resolve().parent; ROOT=HERE.parent
PARENT_SHA='9d09ad1caa0393e847cf0083abee05bebb2e0cf234e82ea7bf0f5e2d146511d0'
TREE='290473b9c04ebe6233ef8dbce24c07011ae8746d'
HEAD='8da225bc46fe1acb24850b67fcc292d5972d2d43'
PARENT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else HERE/'AIOS_0159B_TAM_PROJE.zip'
OUT=HERE/'AIOS_0160_TAM_PROJE.zip'
H=lambda b:hashlib.sha256(b).hexdigest()
def gh(kind,b):return hashlib.sha1((f'{kind} {len(b)}\0').encode()+b).hexdigest()
def safe(base,name):
    p=PurePosixPath(name)
    if p.is_absolute() or '..' in p.parts or '\\' in name or ':' in name:raise ValueError('Unsafe path: '+name)
    return base.joinpath(*p.parts)
def tree(d,root=False):
    entries=[]
    for p in d.iterdir():
        if root and p.name in ('delivery-helper','.git'):continue
        if p.is_symlink():raise ValueError('Symlink not allowed')
        if p.is_dir():entries.append((p.name+'/',b'40000 '+p.name.encode()+b'\0'+bytes.fromhex(tree(p))))
        elif p.is_file():entries.append((p.name,b'100644 '+p.name.encode()+b'\0'+bytes.fromhex(gh('blob',p.read_bytes()))))
    return gh('tree',b''.join(v for k,v in sorted(entries,key=lambda x:x[0].encode())))
def check(b,r):
    if len(b)!=r['bytes'] or H(b)!=r['sha256']:raise ValueError('Hash/length mismatch: '+str(r.get('path','source')))
def writejson(p,o):p.write_bytes((json.dumps(o,ensure_ascii=False,indent=2)+'\n').encode())
if not PARENT.is_file():raise SystemExit('STOP: Place the exact AIOS_0159B_TAM_PROJE.zip in delivery-helper, or pass its path.')
if OUT.exists():raise SystemExit('STOP: output exists; no overwrite.')
if H(PARENT.read_bytes())!=PARENT_SHA:raise ValueError('Wrong 0159-B full archive; SHA-256 mismatch')
if tree(ROOT,True)!=TREE:raise ValueError('Current source tree mismatch; use the exact delivery branch ZIP')
with zipfile.ZipFile(PARENT) as z:
    if z.testzip() is not None:raise ValueError('Parent CRC mismatch')
    pm=json.loads(z.read('MANIFEST_0159B.json'))
    if len(pm['files'])!=222:raise ValueError('Parent manifest count mismatch')
    for r in pm['files']:check(z.read(r['path']),r)
    oldmaster=z.read('AI_Company_OS_DESIGN_MASTER_DOC_REV_0159B_RECOVERY_ADAY.md')
with tempfile.TemporaryDirectory(prefix='.aios0160-',dir=HERE) as td:
    temp=Path(td);d=temp/'full';repo=d/'repository';repo.mkdir(parents=True)
    for p in ROOT.iterdir():
        if p.name in ('delivery-helper','.git'):continue
        if p.is_dir():shutil.copytree(p,repo/p.name)
        elif p.is_file():shutil.copyfile(p,repo/p.name)
    if tree(repo)!=TREE or sum(p.is_file() for p in repo.rglob('*'))!=303:raise ValueError('Repository copy mismatch')
    m=json.loads((repo/'product/SOURCE_MANIFEST.json').read_bytes());assert len(m['files'])==114
    for name,r in m['files'].items():check(safe(repo/'product',name).read_bytes(),r)
    source=d/'AI_Company_OS_Product_v0.1.0_draft6_RECOVERY_R7_SOURCE_ADAY.zip'
    with zipfile.ZipFile(source,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for name in sorted(m['files']):z.write(safe(repo/'product',name),name)
        z.write(repo/'product/SOURCE_MANIFEST.json','SOURCE_MANIFEST.json')
    with zipfile.ZipFile(source) as z:
        if z.testzip() is not None or len(z.namelist())!=115:raise ValueError('Source ZIP mismatch')
        for name,r in m['files'].items():check(z.read(name),r)
    master=d/'AI_Company_OS_DESIGN_MASTER_DOC_REV_0160_RECOVERY_ADAY.md';master.write_bytes(oldmaster+b'\n\n---\n\n'+(repo/'docs/0160/ARCHITECTURE_ADDENDUM.md').read_bytes())
    shutil.copyfile(PARENT,d/'AIOS_0159B_TAM_PROJE.zip')
    writejson(d/'DOGRULAMA_0160.json',{'revision':'0160','status':'STATIC_ONLY_UNRATIFIED','git_head':HEAD,'git_tree':TREE,'repo_files':303,'parent_manifest_pass':222,'parent_sha256':PARENT_SHA,'source_count':114,'source_zip_sha256':H(source.read_bytes()),'master_sha256':H(master.read_bytes()),'master_prefix_exact':True,'static_evidence':json.loads((repo/'handover/VERIFICATION_STATUS.json').read_bytes()),'note':'Locally assembled from exact payload. ZIP compression and timestamps may differ from original delivery candidate; source bytes, parent ZIP and master exact.'})
    (d/'README_0160.md').write_bytes(('# AI Company OS — 0160 tam proje\nGüncel repository 303 dosya, parent 0159-B byte-exact, R7 kaynak 114 kayıt ve güncel master. Git '+HEAD+'; gerçek TEST/CI/PROD NOT_RUN. Başlangıç repository/PROJECT_INDEX.md.\n').encode())
    files=[{'path':p.relative_to(d).as_posix(),'bytes':p.stat().st_size,'sha256':H(p.read_bytes())} for p in sorted(d.rglob('*')) if p.is_file()];assert len(files)==308
    writejson(d/'MANIFEST_0160.json',{'revision':'0160','status':'FULL_PROJECT_WITH_PARENT_ARCHIVE_UNRATIFIED_SOURCE_NOT_RUN','files':files})
    archive=temp/'full.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(d.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(d).as_posix())
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None or len(z.namelist())!=309:raise ValueError('Full ZIP mismatch')
        for r in files:check(z.read(r['path']),r)
    if OUT.exists():raise ValueError('Output appeared; no overwrite')
    os.rename(archive,OUT)
print('PASS: exact parent, 303 repository files, 114 source records, full manifest 308/308.')
print('Full ZIP:',OUT)
