"""0216 isolated D0 reference; NOT independent custody or an execution adapter.
Only a synthetic receipt is committed. No provider, tool, network or T1 callback.
"""
from contextlib import closing, contextmanager
from dataclasses import dataclass, field
from pathlib import Path
import os
import sqlite3


def digest(value):
    return type(value) is str and len(value) == 64 and all(c in '0123456789abcdef' for c in value)


def positive(value):
    return type(value) is int and 0 < value < 2**63


@dataclass(frozen=True)
class Head:
    seq: int
    root_sha: str
    epoch: int

    def validate(self):
        if not (positive(self.seq) and digest(self.root_sha) and positive(self.epoch)):
            raise ValueError('HEAD_SHAPE_HOLD')


@dataclass(frozen=True)
class Intent:
    scope_sha: str
    binding_sha: str
    transaction_ref: str
    request_sha: str

    def validate(self):
        if not (all(digest(x) for x in (self.scope_sha, self.binding_sha, self.request_sha))
                and type(self.transaction_ref) is str and 0 < len(self.transaction_ref) <= 512):
            raise ValueError('INTENT_SHAPE_HOLD')


@dataclass(frozen=True)
class SyntheticReceipt:
    intent: Intent
    head: Head
    status: str = field(default='D0_SYNTHETIC_CONSUMED', init=False)
    external_effect_allowed: bool = field(default=False, init=False)
    independent_verified: bool = field(default=False, init=False)
    retry_allowed: bool = field(default=False, init=False)


class D0EffectFenceReference:
    """Disposable separate SQLite file; no integration with canonical authority."""
    def __init__(self, path):
        p = Path(os.path.abspath(path))
        if not p.name.endswith('.effect-reference.sqlite') or p.resolve() != p or any(x.is_symlink() for x in (p, *p.parents)):
            raise ValueError('REFERENCE_PATH_HOLD')
        self.path = p

    @contextmanager
    def _write(self):
        with closing(sqlite3.connect(self.path.as_uri()+'?mode=rw', uri=True, isolation_level=None, timeout=5)) as db:
            db.execute('PRAGMA trusted_schema=OFF')
            db.execute('BEGIN IMMEDIATE')
            try:
                yield db
                db.execute('COMMIT')
            except BaseException:
                if db.in_transaction:
                    db.execute('ROLLBACK')
                raise

    @classmethod
    def create(cls, path, head):
        if type(head) is not Head:
            raise ValueError('HEAD_SHAPE_HOLD')
        head.validate()
        if head.seq != 1:
            raise ValueError('GENESIS_HOLD')
        obj = cls(path)
        fd = os.open(obj.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        os.close(fd)
        with obj._write() as db:
            db.execute('CREATE TABLE heads(seq INTEGER PRIMARY KEY, root TEXT UNIQUE NOT NULL, epoch INTEGER NOT NULL)')
            db.execute('CREATE TABLE consumed(scope TEXT PRIMARY KEY, binding TEXT UNIQUE NOT NULL, tx TEXT UNIQUE NOT NULL, request TEXT NOT NULL, seq INTEGER NOT NULL, root TEXT NOT NULL, epoch INTEGER NOT NULL)')
            for table in ('heads', 'consumed'):
                for op in ('UPDATE', 'DELETE'):
                    db.execute(f"CREATE TRIGGER {table}_{op} BEFORE {op} ON {table} BEGIN SELECT RAISE(ABORT,'append only'); END")
            db.execute("CREATE TRIGGER heads_insert BEFORE INSERT ON heads WHEN EXISTS(SELECT 1 FROM heads WHERE seq=NEW.seq OR root=NEW.root) BEGIN SELECT RAISE(ABORT,'append only'); END")
            db.execute("CREATE TRIGGER consumed_insert BEFORE INSERT ON consumed WHEN EXISTS(SELECT 1 FROM consumed WHERE scope=NEW.scope OR binding=NEW.binding OR tx=NEW.tx) BEGIN SELECT RAISE(ABORT,'append only'); END")
            db.execute('INSERT INTO heads VALUES (?,?,?)', (head.seq, head.root_sha, head.epoch))
        return obj

    @staticmethod
    def _head(db):
        row = db.execute('SELECT seq,root,epoch FROM heads ORDER BY seq DESC LIMIT 1').fetchone()
        if row is None:
            raise ValueError('HEAD_MISSING_HOLD')
        head = Head(*row)
        head.validate()
        return head

    def advance(self, expected, new):
        if type(expected) is not Head or type(new) is not Head:
            raise ValueError('HEAD_SHAPE_HOLD')
        expected.validate(); new.validate()
        with self._write() as db:
            if self._head(db) != expected or new.seq != expected.seq+1 or new.epoch < expected.epoch or new.root_sha == expected.root_sha:
                raise ValueError('HEAD_CAS_HOLD')
            db.execute('INSERT INTO heads VALUES (?,?,?)', (new.seq,new.root_sha,new.epoch))

    def consume_synthetic(self, expected, intent):
        if type(expected) is not Head or type(intent) is not Intent:
            raise ValueError('INPUT_SHAPE_HOLD')
        expected.validate(); intent.validate()
        with self._write() as db:
            if self._head(db) != expected:
                raise ValueError('STALE_HEAD_HOLD')
            if db.execute('SELECT 1 FROM consumed WHERE scope=? OR binding=? OR tx=?', (intent.scope_sha,intent.binding_sha,intent.transaction_ref)).fetchone():
                raise ValueError('ALREADY_CONSUMED_HOLD')
            db.execute('INSERT INTO consumed VALUES (?,?,?,?,?,?,?)', (intent.scope_sha,intent.binding_sha,intent.transaction_ref,intent.request_sha,expected.seq,expected.root_sha,expected.epoch))
        return SyntheticReceipt(intent,expected)


def external_effect_decision():
    """Unconditional fail-closed reference policy; not wired into live gateways."""
    return 'EXTERNAL_EFFECT_HOLD'
