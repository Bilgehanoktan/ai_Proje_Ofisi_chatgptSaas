"""U2 exact router/wire/HTTP proxy/session diagnostic; persisted reader deliberately replaced by fixture.
Run only in isolated D0 development with reviewed installed Python/Node/TS. No real DB, provider or authority.
"""
import argparse
import os
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import time
from types import ModuleType


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    frontend = root / 'product/ai-company-os-frontend'
    backend = root / 'product/ai-company-os-backend'
    build = args.build.resolve(strict=True)
    sys.path.insert(0, str(backend))
    from app.core.development_review.lifecycle_prefix_wire import prefix_wire
    from fastapi import FastAPI
    import uvicorn
    # Never import or exercise the persisted database reader in this diagnostic.
    module_name = 'app.core.development_review.lifecycle_prefix_projection'
    if module_name in sys.modules:
        raise RuntimeError('fixture reader must be installed before route import')
    fixture = ModuleType(module_name)
    def read_fixture(path):
        if Path(path).resolve() != selector:
            raise ValueError('fixture path mismatch')
        return prefix_wire(int(selector.read_text(encoding='ascii')))
    fixture.read_lifecycle_prefix = read_fixture
    sys.modules[module_name] = fixture
    from app.api.lifecycle_prefix_projection import router
    app = FastAPI()
    app.include_router(router)
    with tempfile.TemporaryDirectory(prefix='aios-u2-') as temp, socket.socket() as sock:
        selector = (Path(temp) / 'prefix.txt').resolve()
        selector.write_text('1', encoding='ascii')
        os.environ['AICOS_D0_LIFECYCLE_PREFIX_DB'] = str(selector)
        for port in range(18355, 18385):
            try:
                sock.bind(('127.0.0.1', port))
                break
            except OSError:
                continue
        else:
            raise RuntimeError('no isolated loopback port')
        sock.listen(128)
        server = uvicorn.Server(uvicorn.Config(app, log_level='error', lifespan='off'))
        worker = threading.Thread(target=server.run, kwargs={'sockets': [sock]}, daemon=True)
        worker.start()
        try:
            deadline = time.monotonic() + 5
            while not server.started and worker.is_alive() and time.monotonic() < deadline:
                time.sleep(.02)
            if not server.started:
                raise RuntimeError('loopback server did not start')
            print('U2: actual FastAPI router + fixture reader + actual TS proxy (not DB)', flush=True)
            subprocess.run([os.environ.get('AICOS_NODE', 'node'), '--test', 'tests/unified-shared-session.test.cjs'], cwd=frontend, env={**os.environ, 'U2_BUILD': str(build), 'U2_FIXTURE_SELECTOR': str(selector), 'AICOS_D0_BACKEND_PORT': str(port)}, check=True, timeout=60)
        finally:
            server.should_exit = True
            worker.join(5)
            if worker.is_alive():
                raise RuntimeError('loopback server did not stop')


if __name__ == '__main__':
    main()
