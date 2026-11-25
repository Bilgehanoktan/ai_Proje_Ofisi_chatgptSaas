"""Interactive D0 preview of the already built and smoke-tested P1 stage."""
import argparse
from pathlib import Path
import socket
import subprocess
import sys
import time
import w8_local as w

APPROVAL = '94a5b62787fdb00cd9e119a856ed7ce7f255debb55da36da0cce0d115690578f'


def launch(stage, frontend_port=17300, backend_port=17301):
    w.installed(stage, APPROVAL)
    if (stage / 'BUILD_TEST_OK').read_text(encoding='utf-8') != APPROVAL:
        raise ValueError('verified build required')
    paths = [w.checked_path(stage, name) for name in (
        'sample-pair/demo.workbench.d0.sqlite',
        'sample-pair/demo.admission.d0.sqlite',
        'demo.review.atomic.d0.sqlite',
    )]
    before = [w.sha(p) for p in paths]
    w.check_ports(frontend_port, backend_port)
    front_origin = f'http://127.0.0.1:{frontend_port}'
    back_origin = f'http://127.0.0.1:{backend_port}'
    env = w.env_local()
    env.update(AICOS_D0_BACKEND_PORT=str(backend_port), AICOS_D0_WORKBENCH_DB=str(paths[0]),
               AICOS_D0_ADMISSION_DB=str(paths[1]),
               AICOS_D0_REVIEW_DB=str(paths[2]))
    f, b = w.frontend(stage), w.backend(stage)
    procs = []
    try:
        procs.append(subprocess.Popen([str(w.python(stage)), '-m', 'uvicorn',
            'app.main:app', '--host', '127.0.0.1', '--port', str(backend_port)], cwd=b, env=env))
        w.ready(back_origin+'/demo/v1/status', procs[-1])
        procs.append(subprocess.Popen([w.node(), str(f / 'node_modules/next/dist/bin/next'),
            'start', '-H', '127.0.0.1', '-p', str(frontend_port)], cwd=f, env=env))
        w.ready(front_origin+'/', procs[-1])
        routes = {'mvp': 'mvp/diagnostics', 'admission': 'admission/sample-projection',
                  'outbox': 'outbox/review-projection', 'office-workbench': 'office/workbench-projection',
                  'task-budget': 'task-budget/sample-projection'}
        for front, back in routes.items():
            x = w.get_json(back_origin+'/demo/v1/' + back)
            y = w.get_json(front_origin+'/api/demo/' + front)
            if x != y:
                raise ValueError('loopback parity mismatch: ' + front)
            if front == 'task-budget' and (x['budget']['phase'] != 'UNKNOWN_HOLD'
                or x['budget']['sample_reserved_minor'] != 100
                or x['spend_allowed'] is not False):
                raise ValueError('paired invariant mismatch')
        print('D0 READY: '+front_origin+'/office', flush=True)
        print('Keep this console open. Ctrl+C stops both servers. Synthetic read-only preview.', flush=True)
        while True:
            if any(p.poll() is not None for p in procs):
                raise ValueError('local server exited')
            time.sleep(1)
    except KeyboardInterrupt:
        print('Stopping D0 preview...', flush=True)
    finally:
        for p in reversed(procs):
            if p.poll() is None:
                p.terminate()
                try:
                    p.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    p.kill()
                    p.wait()
        if before != [w.sha(p) for p in paths]:
            raise ValueError('sample database changed')
        print('D0 sample DB hashes unchanged', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage', type=Path, required=True)
    parser.add_argument('--frontend-port',type=int,default=17300)
    parser.add_argument('--backend-port',type=int,default=17301)
    args = parser.parse_args()
    try:
        launch(args.stage.resolve(),args.frontend_port,args.backend_port)
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('HOLD:', exc, file=sys.stderr)
        sys.exit(1)
