"""Create or inspect one explicit local synthetic outbox review file, never send."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
from .outbox_claim_sample import OutboxReviewSample, read_projection


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('create','snapshot'))
    p.add_argument('--db',type=Path,required=True)
    args=p.parse_args()
    if args.mode=='create':
        s=OutboxReviewSample(args.db)
        s.create()
        s.renew('demo-owner',None,1,10)
        s.observe('demo-command','demo-owner',1,2,0)
        s.claim_review('demo-command','demo-reviewer',3,5)
        s.mark_unknown('demo-command','demo-reviewer',1,4)
        s.record_readback('demo-command',1,sha256(b'D0 sample readback, not evidence').hexdigest())
    print(json.dumps(read_projection(args.db),ensure_ascii=False,sort_keys=True))


if __name__=='__main__': main()
