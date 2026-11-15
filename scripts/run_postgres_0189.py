"""Run the existing 0183 DDL probe in a fresh socket-only PostgreSQL cluster.
No DSN, existing database, production migration, or canonical T1 acceptance.
Run as a non-root local development user on POSIX with PostgreSQL binaries installed.
"""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile

PIN = 'a283d0c0b10294b824de0f34f431aeeeb1fb2071cde7d7f81bb62a4faf716d59'
ROOT = Path(__file__).resolve().parents[1]
DDL = ROOT / 'database/migrations/0183_D0_PHYSICAL_CANDIDATE.sql'
PROBE = ROOT / 'tests/integration/postgres_0183_probe.sql'


def compose(ddl: bytes, probe: bytes) -> bytes:
    if hashlib.sha256(ddl).hexdigest() != PIN or not ddl.endswith(b'ROLLBACK;\n'):
        raise ValueError('PG_DDL_PIN_HOLD')
    if not probe.endswith(b'ROLLBACK;\n'):
        raise ValueError('PG_PROBE_ROLLBACK_HOLD')
    return ddl[:-len(b'ROLLBACK;\n')] + probe


def binaries(bindir: Path) -> dict[str, str]:
    result = {}
    for name in ('initdb', 'pg_ctl', 'psql'):
        path = bindir / name
        if not path.is_file() or not os.access(path, os.X_OK):
            raise FileNotFoundError(f'PG_BINARY_MISSING: {name}')
        result[name] = str(path.resolve())
    return result


def run(bindir: Path) -> None:
    exe = binaries(bindir)
    sql = compose(DDL.read_bytes(), PROBE.read_bytes())
    if os.name != 'posix' or os.geteuid() == 0:
        raise PermissionError('PG_PROBE_REQUIRES_NON_ROOT_POSIX_USER')
    env = {k: v for k, v in os.environ.items() if not k.upper().startswith('PG')}
    env['LC_ALL'] = 'C'
    # A failed stop retains the private cluster directory for manual cleanup.
    root = Path(tempfile.mkdtemp(prefix='aicos0189-', dir='/tmp'))
    data = root / 'data'; sock = root / 'socket'; sock.mkdir(mode=0o700)
    import shutil
    safe_to_remove = True
    try:
        def cmd(name, *args, **kw):
            return subprocess.run([exe[name], *map(str,args)], env=env, check=True, timeout=40, **kw)
        cmd('initdb','-D',data,'--auth=trust','--no-locale','--encoding=UTF8','-U','aicos_bootstrap', stdout=subprocess.DEVNULL)
        started = False
        try:
            # Private directory and socket only; never listen on TCP or reuse a cluster.
            safe_to_remove = False
            cmd('pg_ctl','-D',data,'-l',root/'server.log','-o',f"-h '' -k {sock} -p 55489",'-w','start', stdout=subprocess.DEVNULL)
            started = True
            args = ('-X','--no-password','-v','ON_ERROR_STOP=1','-h',sock,'-p','55489','-U','aicos_bootstrap','-d','postgres')
            cmd('psql',*args,input=sql)
            r = cmd('psql',*args,'-Atc',"SELECT (to_regnamespace('aicos_d0_candidate') IS NULL AND NOT EXISTS (SELECT FROM pg_roles WHERE rolname='aicos_0189_probe'))::text",capture_output=True,text=True)
            if r.stdout.strip() != 'true':
                raise RuntimeError('PG_ROLLBACK_READBACK_HOLD')
            print('PASS 09 outer rollback removes schema and probe role')
        finally:
            if started or (data/'postmaster.pid').exists():
                # Do not delete a live cluster if stop fails. Surface failure.
                cmd('pg_ctl','-D',data,'-m','fast','-w','stop',stdout=subprocess.DEVNULL)
                safe_to_remove = True
    finally:
        if safe_to_remove:
            shutil.rmtree(root)
        else:
            print(f'PG_PROBE_CLEANUP_HOLD: {root}')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--bindir',type=Path,required=True,help='directory containing trusted installed PostgreSQL executables')
    a = p.parse_args()
    run(a.bindir)


if __name__ == '__main__':
    main()
