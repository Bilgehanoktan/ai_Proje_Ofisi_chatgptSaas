"""Explicit ORG R5 fixture launcher; never contacts D3/D4 or production.
Default is preflight only. Existing R5 SQL/runner and R5R2 reviewer are reused.
"""
import argparse
import hashlib
import getpass
import warnings
import importlib.metadata
import os
from pathlib import Path
import re
import socket
import subprocess
import sys

PORT = 55435
CLUSTER = 'aicos_org_r5_disposable'
DATABASE = 'aicos_org_r4_disposable'
ADMIN = 'org_r5_admin'
REVIEW_SHA = 'c5bad78cf6c139a40f012eb986a1f0993b3d904a7f786664f8ef1ff4e921550e'

class Hold(RuntimeError):
    pass


def require(condition, code):
    if not condition:
        raise Hold(code)


def parse_version(text):
    match = re.fullmatch(r'[^\r\n]+ \(PostgreSQL\) 17\.([0-9]+)(?: [^\r\n]+)?', text.strip())
    require(match is not None, 'PG17_BINARY_REQUIRED')
    minor = int(match.group(1))
    require(0 <= minor < 10000, 'PG_VERSION_FORMAT')
    return 170000 + minor


def validate_paths(stage, report):
    require(stage.is_absolute() and report.is_absolute(), 'ABSOLUTE_PATHS_REQUIRED')
    require(not os.path.lexists(stage) and not os.path.lexists(report), 'FRESH_STAGE_AND_REPORT_REQUIRED')
    require(stage.parent.is_dir() and report.parent.is_dir(), 'PARENT_DIRECTORY_REQUIRED')
    require(stage != report and stage not in report.parents and report not in stage.parents, 'PATH_OVERLAP')
    require(stage.parent.resolve() == stage.parent and report.parent.resolve() == report.parent, 'RESOLVED_PARENT_REQUIRED')


def verify_identity(output, stage, version):
    fields = output.strip().split('|')
    require(len(fields) == 7, 'IDENTITY_SHAPE')
    require(fields[:3] == [CLUSTER, str(PORT), str(version)], 'IDENTITY_CLUSTER_PORT_VERSION')
    require(Path(fields[3]).resolve() == stage.resolve(), 'IDENTITY_DATA_DIRECTORY')
    require(fields[4:] == [ADMIN, ADMIN, '127.0.0.1'], 'IDENTITY_ADMIN_LOOPBACK')


def check_port():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if os.name == 'nt':
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            sock.bind(('127.0.0.1', PORT))
    except OSError as exc:
        raise Hold('ORG_PORT_55435_UNAVAILABLE') from exc


def env_without_pg():
    return {k: v for k, v in os.environ.items() if not k.upper().startswith('PG')}


def read_admin_password():
    """Read from the terminal, never argv, files, or inherited environment."""
    with warnings.catch_warnings():
        warnings.simplefilter('error', getpass.GetPassWarning)
        password = getpass.getpass('ORG disposable admin password: ')
    require(bool(password), 'ADMIN_PASSWORD_REQUIRED')
    return password


def admin_env(env, password):
    require(bool(password), 'ADMIN_PASSWORD_REQUIRED')
    return {**env, 'PGPASSWORD': password, 'PGCLIENTENCODING': 'UTF8'}


def validate_recovery(stage, report):
    require(stage.is_absolute() and report.is_absolute(), 'ABSOLUTE_PATHS_REQUIRED')
    require(stage.is_dir() and not stage.is_symlink() and stage.resolve() == stage, 'RECOVERY_STAGE_REQUIRED')
    require(not os.path.lexists(report), 'RECOVERY_REPORT_EXISTS')
    require(stage != report and stage not in report.parents and report not in stage.parents, 'PATH_OVERLAP')
    require((stage / 'PG_VERSION').is_file() and (stage / 'PG_VERSION').read_text(encoding='ascii').strip() == '17', 'RECOVERY_PG17_REQUIRED')


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--pg-bin', type=Path, required=True)
    p.add_argument('--stage', type=Path, required=True)
    p.add_argument('--report', type=Path, required=True)
    mode = p.add_mutually_exclusive_group()
    mode.add_argument('--execute-disposable', action='store_true')
    mode.add_argument('--stop-verified-stage', action='store_true')
    args = p.parse_args(argv)
    stage, report = args.stage, args.report
    started = False
    try:
        if args.stop_verified_stage:
            validate_recovery(stage, report)
        else:
            validate_paths(stage, report)
        candidates = Path(__file__).resolve().parent.parent
        r5 = candidates / 'ORG-05R5'
        reviewer = candidates / 'ORG-05R5R2' / 'review_pg_evidence.py'
        require(reviewer.is_file() and hashlib.sha256(reviewer.read_bytes()).hexdigest() == REVIEW_SHA, 'REVIEW_SOURCE_PIN')
        env = env_without_pg()
        def run(command, capture=False, password=None):
            child_env = env if password is None else admin_env(env, password)
            return subprocess.run([str(x) for x in command], check=True, env=child_env, text=True, encoding='utf-8' if password is not None and capture else None, stdout=subprocess.PIPE if capture else None).stdout
        review_cmd = [sys.executable, '-B', reviewer, '--candidates', candidates]
        run(review_cmd)
        require(importlib.metadata.version('psycopg') == '3.3.9' and importlib.metadata.version('psycopg-binary') == '3.3.9', 'DRIVER_PIN')
        import psycopg
        require(psycopg.pq.__impl__ == 'binary', 'DRIVER_BINARY_REQUIRED')
        require(args.pg_bin.is_absolute() and args.pg_bin.is_dir(), 'PG_BIN_DIRECTORY')
        suffix = '.exe' if os.name == 'nt' else ''
        bins = {n: args.pg_bin / (n + suffix) for n in ('initdb', 'pg_ctl', 'psql', 'postgres')}
        require(all(f.is_file() for f in bins.values()), 'PG_BIN_MISSING')
        versions = [parse_version(run([f, '--version'], True)) for f in bins.values()]
        require(len(set(versions)) == 1, 'PG_BINARY_VERSION_MISMATCH')
        version = versions[0]
        base = [bins['psql'], '-X', '-w', '-v', 'ON_ERROR_STOP=1', '-h', '127.0.0.1', '-p', str(PORT), '-U', ADMIN]
        sql = "SELECT current_setting('cluster_name'),current_setting('port'),current_setting('server_version_num'),current_setting('data_directory'),current_user,session_user,host(inet_server_addr());"
        def authenticate(password):
            identity = run(base + ['-d', 'postgres', '-A', '-t', '-c', sql], True, password)
            verify_identity(identity, stage, version)
        if args.stop_verified_stage:
            status = subprocess.run([str(bins['pg_ctl']), '-D', str(stage), 'status'], env=env, check=False)
            if status.returncode == 3:
                check_port()
                print('ORG_STAGE_ALREADY_STOPPED; files preserved', flush=True)
                return 0
            require(status.returncode == 0, 'RECOVERY_STATUS_HOLD')
            password = read_admin_password()
            try:
                authenticate(password)
            finally:
                del password
            run([bins['pg_ctl'], '-D', stage, '-w', 'stop', '-m', 'fast'])
            check_port()
            print('VERIFIED_ORG_STAGE_STOPPED; files preserved', flush=True)
            return 0
        check_port()
        print('SOURCE/DRIVER/BINARY/PORT PREFLIGHT PASS; PostgreSQL tests NOT_RUN', flush=True)
        if not args.execute_disposable:
            return 0
        validate_paths(stage, report)
        check_port()
        run([bins['initdb'], '-D', stage, '--username=' + ADMIN, '--auth=scram-sha-256', '--locale-provider=libc', '--locale=C', '--encoding=UTF8', '--pwprompt'])
        run([bins['pg_ctl'], '-D', stage, '-l', stage / 'server.log', '-o', f'-p {PORT} -h 127.0.0.1 -c cluster_name={CLUSTER}', '-w', 'start'])
        started = True
        password = read_admin_password()
        try:
            authenticate(password)
            run(base + ['-d', 'postgres', '-f', r5 / 'bootstrap_roles.sql'], password=password)
            run(base + ['-d', DATABASE, '-f', candidates / 'ORG-05R4' / 'PG_SCHEMA_R4.sql'], password=password)
        finally:
            del password
        run([sys.executable, '-B', r5 / 'run_pg_acceptance.py', '--execute-disposable', '--port', str(PORT), '--report', report])
        run(review_cmd + ['--report', report])
        run([bins['pg_ctl'], '-D', stage, '-w', 'stop', '-m', 'fast'])
        started = False
        print('COMPLETE_REPORT_UNATTESTED; raw evidence review and product acceptance HOLD', flush=True)
        return 0
    except (Hold, OSError, subprocess.SubprocessError, importlib.metadata.PackageNotFoundError, ImportError, getpass.GetPassWarning, EOFError, KeyboardInterrupt) as exc:
        print('HOLD: ' + (str(exc) if isinstance(exc, Hold) else type(exc).__name__), file=sys.stderr)
        if started or os.path.lexists(stage):
            print('Preserve the new stage and logs; do not retry or delete. Stop only the verified ORG cluster manually.', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
