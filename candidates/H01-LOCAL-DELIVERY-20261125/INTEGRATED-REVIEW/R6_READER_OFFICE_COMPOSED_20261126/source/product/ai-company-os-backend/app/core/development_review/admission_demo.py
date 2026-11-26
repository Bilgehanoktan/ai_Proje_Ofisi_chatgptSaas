"""Explicit disposable local D0 demonstration; no external effects."""
import argparse
import json
from .admission_sample import AdmissionSample, OWNER, read_admission


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('create','admit','known','unknown','snapshot'))
    p.add_argument('--db',required=True)
    a=p.parse_args(); store=AdmissionSample(a.db)
    if a.mode=='create': store.create()
    elif a.mode!='snapshot':
        kind={'admit':'ADMIT','known':'KNOWN_SAMPLE','unknown':'UNKNOWN'}[a.mode]
        store.apply(OWNER,kind,0 if kind=='ADMIT' else 1)
    print(json.dumps(read_admission(a.db),sort_keys=True))


if __name__=='__main__': main()
