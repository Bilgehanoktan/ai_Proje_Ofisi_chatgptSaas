"""Explicit local CLI for the pinned synthetic workbench; never an ASGI mutation route."""
import argparse
import json
from pathlib import Path
from .sandbox_store import Workbench


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('create', 'snapshot'))
    parser.add_argument('--db', type=Path, required=True)
    args = parser.parse_args()
    fixture = Path(__file__).resolve().parents[3]/'fixtures/core.preview.json'
    plan = json.loads(fixture.read_text(encoding='utf-8'))['plan']
    wb = Workbench(args.db, plan)
    if args.mode == 'create':
        wb.create()
        for tick, task in enumerate(('plan','draft','research','merge','qa'), 1):
            fence = wb.lease(task,'demo-holder',tick,10)
            wb.observe(task,'demo-holder',fence,tick,'demo-command-'+task)
    print(json.dumps(wb.snapshot(), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
