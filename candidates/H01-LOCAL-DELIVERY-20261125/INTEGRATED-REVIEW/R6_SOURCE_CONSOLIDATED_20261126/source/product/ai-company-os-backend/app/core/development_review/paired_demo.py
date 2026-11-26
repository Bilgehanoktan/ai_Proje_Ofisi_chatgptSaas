"""Explicit fresh paired D0 sample creation. No cross-file atomicity or actual execution."""
import argparse
import json
from pathlib import Path
from .admission_sample import AdmissionSample, OWNER
from .sandbox_store import Workbench
from .task_budget_snapshot import new_pair_id, read_task_budget_snapshot


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--directory', type=Path, required=True)
    p.add_argument('--outcome', choices=('reserved','known','unknown'), default='reserved')
    a = p.parse_args()
    # Exclusive directory: failure leaves a disposable partial pair for explicit inspection.
    a.directory.mkdir(exist_ok=False)
    w = a.directory/'demo.workbench.d0.sqlite'
    b = a.directory/'demo.admission.d0.sqlite'
    fixture = Path(__file__).resolve().parents[3]/'fixtures/core.preview.json'
    plan = json.loads(fixture.read_text(encoding='utf-8'))['plan']
    pair = new_pair_id()
    wb, admission = Workbench(w, plan), AdmissionSample(b)
    wb.create(pair_id=pair)
    admission.create(pair_id=pair)
    admission.apply(OWNER,'ADMIT',0)
    for tick, task in enumerate(('plan','draft','research','merge','qa'),1):
        fence = wb.lease(task,'demo-holder',tick,10)
        wb.observe(task,'demo-holder',fence,tick,'demo-command-'+task)
    if a.outcome != 'reserved':
        admission.apply(OWNER,{'known':'KNOWN_SAMPLE','unknown':'UNKNOWN'}[a.outcome],1)
    print(json.dumps(read_task_budget_snapshot(w,b),sort_keys=True))


if __name__ == '__main__':
    main()
