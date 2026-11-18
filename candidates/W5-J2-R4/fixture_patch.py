"""Pinned, additive R2 fixture revision; never patch or import product source.
Generate only in a disposable test stage. No PostgreSQL, grant or provider.
"""
from hashlib import sha256
from pathlib import Path

R2_SHA = '3ba94906c626034c9b0a01758e6cc2bccdab71206decf6a222e51898fbf70e53'

PATCHES = (
    ("require(not closed or (free==0 and not rows),'NO_EFFECT_RELEASE_HOLD')",
     "require((not closed and released==0) or (closed and free==0 and "
     "all(r[2]=='RECONCILED' for r in rows) and released==issued-sum(r[1] for r in rows)),"
     "'TERMINAL_REMAINDER_HOLD')"),
    ("elif kind=='CLOSE_UNUSED':\n                require(tx not in receipts and db.execute('SELECT 1 FROM pool WHERE run=? AND closed=1',(target,)).fetchone(),'JOURNAL_RELEASE_DRIFT_HOLD')",
     "elif kind in ('CLOSE_UNUSED','CLOSE_PARTIAL'):\n"
     "                require(tx not in receipts and db.execute('SELECT 1 FROM pool WHERE run=? AND closed=1',(target,)).fetchone(),'JOURNAL_RELEASE_DRIFT_HOLD')\n"
     "                historical=db.execute('SELECT 1 FROM member WHERE run=? LIMIT 1',(target,)).fetchone() is not None\n"
     "                require(historical==(kind=='CLOSE_PARTIAL'),'JOURNAL_CLOSE_KIND_HOLD')"),
    ("if v[0]=='CLOSE_UNUSED')", "if v[0] in ('CLOSE_UNUSED','CLOSE_PARTIAL'))"),
    ("    def readback(self,budget):", '''    def close_partial(self,budget,run,expected_revision,tx,*,fault=None):
        """R4 fixture only: settle all members before releasing the unallocated remainder.
        No reallocation of released capacity, no effect grant, no live terminal transition.
        """
        with self._transaction(budget,expected_revision,tx,'CLOSE_PARTIAL',run,fault=fault) as db:
            issued,free,closed,owner,released=self._pool(db,run,budget)
            rows=db.execute('SELECT state,amount FROM member WHERE run=? AND budget=?',(run,budget)).fetchall()
            require(not closed and released==0 and bool(rows) and all(s=='RECONCILED' for s,_ in rows), 'PARTIAL_CLOSE_MEMBERSHIP_HOLD')
            require(free==issued-sum(a for _,a in rows),'PARTIAL_CLOSE_CONSERVATION_HOLD')
            require(db.execute('UPDATE pool SET free=0,closed=1,released=? WHERE run=? AND budget=? AND closed=0 AND free=?',(free,run,budget,free)).rowcount==1,'PARTIAL_CLOSE_POOL_CAS_HOLD')
            self._fault(fault,'after_pool')
            require(db.execute('UPDATE b SET outstanding=outstanding-? WHERE id=? AND outstanding>=? AND unknown=0',(free,budget,free)).rowcount==1,'BALANCE_HOLD')
            self._fault(fault,'after_release')

    def readback(self,budget):'''),
)


def build_fixture(raw: bytes) -> bytes:
    if type(raw) is not bytes or sha256(raw).hexdigest()!=R2_SHA:
        raise ValueError('R2_FIXTURE_PIN_HOLD')
    source=raw.decode('utf-8')
    for old,new in PATCHES:
        if source.count(old)!=1:
            raise ValueError('R2_PATCH_CONTEXT_HOLD')
        source=source.replace(old,new,1)
    return source.encode('utf-8')


def write_fixture(source: Path, target: Path):
    if target.exists() or source.resolve()==target.resolve():
        raise ValueError('FRESH_FIXTURE_TARGET_REQUIRED')
    raw=build_fixture(source.read_bytes())
    with target.open('xb') as output:
        output.write(raw)
    return sha256(raw).hexdigest()
