"""D5-G1: internal D0 bearer-session lookup, not a grant or live IAM service.
Bootstrap records and clock are trusted server-side inputs; no public issuer.
G2 optionally persists D0 state inside the existing authority SQLite boundary.
No live owner publication, trusted clock, ORG permission or independent custody.
"""
from dataclasses import dataclass, field
from hashlib import sha256
from hmac import compare_digest
from threading import RLock
from time import monotonic
import re
import json
import sqlite3
from contextlib import closing
from dataclasses import asdict

D0_SCOPE = ('synthetic-tenant', 'synthetic-company', 'A0_SAMPLE_ONLY')
MAX_TTL = 900  # D0 seconds, not a production session policy.


def credential_digest(credential):
    # Canonical encoding of exactly 32 random bytes (base64url, no padding).
    if type(credential) is not str or re.fullmatch(r'[A-Za-z0-9_-]{42}[AEIMQUYcgkosw048]', credential) is None:
        raise ValueError('IAM_CREDENTIAL_HOLD')
    return sha256(credential.encode('ascii')).hexdigest()


def _demo_id(value):
    return type(value) is str and re.fullmatch(r'demo-[A-Za-z0-9][A-Za-z0-9_.:-]{0,122}', value) is not None


def _tick(value):
    return type(value) is int and 0 <= value < 2**63


@dataclass(frozen=True)
class SessionRecord:
    session_id: str
    credential_sha256: str = field(repr=False)
    principal_id: str
    kind: str
    scope: tuple[str, str, str]
    agent_instance_id: str | None
    issued: int
    expires: int


@dataclass(frozen=True)
class SessionObservation:
    principal_id: str
    kind: str
    scope: tuple[str, str, str]
    agent_instance_id: str | None
    session_id: str
    expires: int
    revision: int
    decision: str = field(default='HOLD', init=False)
    grant_allowed: bool = field(default=False, init=False)
    dispatch_allowed: bool = field(default=False, init=False)


class D0SessionResolver:
    """Server-owned synthetic process-local registry; caller cannot supply identity."""

    def __init__(self, records, *, clock=None):
        if type(records) is not tuple or not 1 <= len(records) <= 1024:
            raise ValueError('IAM_BOOTSTRAP_HOLD')
        self._records = {}
        hashes = set()
        for r in records:
            if (type(r) is not SessionRecord or not _demo_id(r.session_id)
                    or not _demo_id(r.principal_id) or type(r.credential_sha256) is not str
                    or re.fullmatch(r'[0-9a-f]{64}', r.credential_sha256) is None
                    or type(r.scope) is not tuple or r.scope != D0_SCOPE
                    or r.kind not in ('HUMAN', 'AGENT')
                    or (r.kind == 'HUMAN' and r.agent_instance_id is not None)
                    or (r.kind == 'AGENT' and not _demo_id(r.agent_instance_id))
                    or not _tick(r.issued) or not _tick(r.expires)
                    or not 0 < r.expires - r.issued <= MAX_TTL
                    or r.session_id in self._records or r.credential_sha256 in hashes):
                raise ValueError('IAM_BOOTSTRAP_HOLD')
            self._records[r.session_id] = r
            hashes.add(r.credential_sha256)
        self._clock = clock if clock is not None else lambda: int(monotonic())
        if not callable(self._clock):
            raise ValueError('IAM_CLOCK_HOLD')
        self._lock = RLock()
        self._revoked = set()
        self._revision = 1
        self._last_tick = None
        self._clock_failed = False
        self._authority = None
        self._pin = None
        self._domain = None
        self._root = None

    def _now(self):
        if self._clock_failed:
            return None
        try:
            now = self._clock()
            if not _tick(now) or (self._last_tick is not None and now < self._last_tick):
                raise ValueError('clock')
        except Exception:
            self._clock_failed = True
            return None
        self._last_tick = now
        return now

    def resolve(self, credential, *, expected_scope):
        """Resolve opaque credential; never accept caller-supplied principal or time."""
        if self._authority is not None:
            return self._resolve_durable(credential, expected_scope)
        if type(expected_scope) is not tuple or expected_scope != D0_SCOPE:
            return None
        try:
            digest = credential_digest(credential)
        except ValueError:
            return None
        with self._lock:
            now = self._now()
            if now is None:
                return None
            # All records are compared, no early exit on the secret match.
            matched = [r for r in self._records.values() if compare_digest(digest, r.credential_sha256)]
            if len(matched) != 1:
                return None
            r = matched[0]
            if r.session_id in self._revoked or not r.issued <= now < r.expires:
                return None
            return SessionObservation(r.principal_id, r.kind, r.scope, r.agent_instance_id,
                                      r.session_id, r.expires, self._revision)

    def revoke_local(self, session_id, *, expected_revision):
        """Trusted bootstrap owner only; local CAS, never protected publication."""
        if self._authority is not None:
            return self._revoke_durable(session_id, expected_revision)
        with self._lock:
            if (not _demo_id(session_id) or not _tick(expected_revision)
                    or expected_revision != self._revision or session_id not in self._records
                    or session_id in self._revoked or self._revision >= 2**63-1):
                return False
            self._revoked.add(session_id)
            self._revision += 1
            return True


    @staticmethod
    def _state(db, root, domain):
        from app.core.transaction.intent_authority import D0IntentAuthority
        seq, observed = D0IntentAuthority._head(db)
        if observed != root:
            raise ValueError('IAM_ROOT_HOLD')
        if db.execute('SELECT id FROM iam_bootstrap').fetchall() != [(1,)]:
            raise ValueError('IAM_BOOTSTRAP_HOLD')
        meta = db.execute('SELECT domain FROM iam_meta WHERE id=1').fetchall()
        if meta != [(domain,)]:
            raise ValueError('IAM_DOMAIN_HOLD')
        rows = db.execute('SELECT session_id, credential_sha, principal, kind, agent, issued, expires FROM iam_sessions ORDER BY session_id').fetchall()
        records = tuple(SessionRecord(i,h,p,k,D0_SCOPE,a,t,e) for i,h,p,k,a,t,e in rows)
        # Reuse G1 validation, not a parallel credential registry implementation.
        D0SessionResolver(records)
        revocations = db.execute('SELECT revision, session_id FROM iam_revocations ORDER BY revision').fetchall()
        ids = {r.session_id for r in records}
        if (any(n != i or sid not in ids for i,(n,sid) in enumerate(revocations,2))
                or len({sid for _,sid in revocations}) != len(revocations)):
            raise ValueError('IAM_HISTORY_HOLD')
        pin = sha256(json.dumps(['d5-g2-d0',seq,asdict(root),domain,
                    [asdict(r) for r in records],revocations],sort_keys=True,
                    separators=(',',':'),ensure_ascii=True).encode('ascii')).hexdigest()
        return records, {sid for _,sid in revocations}, len(revocations)+1, pin

    @classmethod
    def bootstrap_durable(cls, path, root, records, *, domain, clock):
        """Exclusive new D0 authority file; no migration or rehydration of old credentials."""
        from app.core.transaction.intent_authority import D0IntentAuthority
        if not _demo_id(domain) or not callable(clock):
            raise ValueError('IAM_DOMAIN_HOLD')
        cls(records, clock=clock)
        authority = D0IntentAuthority.create(path, root, iam_bootstrap=True)
        with closing(authority._db()) as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('CREATE TABLE iam_meta(id INTEGER PRIMARY KEY CHECK(id=1), domain TEXT NOT NULL)')
            db.execute('CREATE TABLE iam_sessions(session_id TEXT PRIMARY KEY, credential_sha TEXT UNIQUE NOT NULL, principal TEXT NOT NULL, kind TEXT NOT NULL, agent TEXT, issued INTEGER NOT NULL, expires INTEGER NOT NULL)')
            db.execute('CREATE TABLE iam_revocations(revision INTEGER PRIMARY KEY, session_id TEXT UNIQUE NOT NULL)')
            db.execute('CREATE TABLE iam_claim_pins(scope_sha TEXT PRIMARY KEY, session_sha TEXT NOT NULL)')
            db.execute('CREATE TABLE iam_clock(id INTEGER PRIMARY KEY CHECK(id=1), tick INTEGER NOT NULL, fault INTEGER NOT NULL CHECK(fault IN (0,1)))')
            db.execute('INSERT INTO iam_meta VALUES (1,?)',(domain,))
            now = clock()
            if not _tick(now):
                raise ValueError('IAM_CLOCK_HOLD')
            db.execute('INSERT INTO iam_clock VALUES (1,?,0)',(now,))
            for r in records:
                db.execute('INSERT INTO iam_sessions VALUES (?,?,?,?,?,?,?)',(r.session_id,r.credential_sha256,r.principal_id,r.kind,r.agent_instance_id,r.issued,r.expires))
            for table in ('iam_meta','iam_sessions','iam_revocations','iam_claim_pins'):
                for op in ('UPDATE','DELETE'):
                    db.execute(f"CREATE TRIGGER {table}_no_{op.lower()} BEFORE {op} ON {table} BEGIN SELECT RAISE(ABORT,'append only'); END")
                key = {'iam_meta':'id','iam_sessions':'session_id','iam_revocations':'revision','iam_claim_pins':'scope_sha'}[table]
                db.execute(f"CREATE TRIGGER {table}_no_replace BEFORE INSERT ON {table} WHEN EXISTS(SELECT 1 FROM {table} WHERE {key}=NEW.{key}) BEGIN SELECT RAISE(ABORT,'append only'); END")
            db.execute("CREATE TRIGGER iam_sessions_sealed BEFORE INSERT ON iam_sessions BEGIN SELECT RAISE(ABORT,'sealed'); END")
            db.execute("CREATE TRIGGER iam_meta_sealed BEFORE INSERT ON iam_meta BEGIN SELECT RAISE(ABORT,'sealed'); END")
            db.execute("CREATE TRIGGER iam_revocations_no_alias BEFORE INSERT ON iam_revocations WHEN EXISTS(SELECT 1 FROM iam_revocations WHERE session_id=NEW.session_id) BEGIN SELECT RAISE(ABORT,'append only'); END")
            pin = cls._state(db,root,domain)[3]
            db.execute('COMMIT')
        return cls.open_durable(authority,root,expected_pin=pin,domain=domain,clock=clock)

    @classmethod
    def open_durable(cls, authority, root, *, expected_pin, domain, clock):
        """Owner-retained pin required; never infer it from restored data."""
        from app.core.transaction.intent_authority import D0IntentAuthority, RootPin, _digest
        if (type(authority) is not D0IntentAuthority or type(root) is not RootPin
                or not _digest(expected_pin) or not _demo_id(domain) or not callable(clock)):
            raise ValueError('IAM_OPEN_HOLD')
        with closing(authority._db()) as db:
            db.execute('BEGIN IMMEDIATE')
            records, _, _, pin = cls._state(db,root,domain)
            if pin != expected_pin:
                raise ValueError('IAM_PIN_HOLD')
            obj = cls(records,clock=clock)
            obj._authority, obj._root, obj._domain, obj._pin = authority, root, domain, pin
            if obj._durable_now(db, persist=True) is None:
                db.execute('COMMIT')
                raise ValueError('IAM_CLOCK_HOLD')
            db.execute('COMMIT')
        return obj

    @property
    def durable_pin(self):
        return self._pin

    def _durable_now(self, db, *, persist):
        row = db.execute('SELECT tick,fault FROM iam_clock WHERE id=1').fetchone()
        if row is None or not _tick(row[0]) or row[1] != 0:
            return None
        with self._lock:
            now = self._now()
            if now is None or now < row[0]:
                self._clock_failed = True
                if persist:
                    db.execute('UPDATE iam_clock SET fault=1 WHERE id=1')
                return None
        if persist:
            db.execute('UPDATE iam_clock SET tick=? WHERE id=1',(now,))
        return now

    def _read_durable(self, db, credential, expected_scope, *, persist_clock):
        if type(expected_scope) is not tuple or expected_scope != D0_SCOPE:
            return None
        digest = credential_digest(credential)
        records, revoked, revision, pin = self._state(db,self._root,self._domain)
        if pin != self._pin:
            return None
        now = self._durable_now(db,persist=persist_clock)
        if now is None:
            return None
        matched = [r for r in records if compare_digest(digest,r.credential_sha256)]
        if len(matched)!=1:
            return None
        r = matched[0]
        if r.session_id in revoked or not r.issued <= now < r.expires:
            return None
        return SessionObservation(r.principal_id,r.kind,r.scope,r.agent_instance_id,r.session_id,r.expires,revision)

    def _resolve_durable(self, credential, expected_scope):
        try:
            with closing(self._authority._db()) as db:
                db.execute('BEGIN IMMEDIATE')
                result = self._read_durable(db,credential,expected_scope,persist_clock=True)
                db.execute('COMMIT')
                return result
        except (ValueError,sqlite3.Error,OSError):
            return None

    def _revoke_durable(self, session_id, expected_revision):
        if not _demo_id(session_id) or not _tick(expected_revision):
            return False
        try:
            with closing(self._authority._db()) as db:
                db.execute('BEGIN IMMEDIATE')
                records, revoked, revision, pin = self._state(db,self._root,self._domain)
                if (pin != self._pin or revision != expected_revision or revision >= 2**63-1
                        or session_id in revoked or session_id not in {r.session_id for r in records}):
                    return False
                if self._durable_now(db,persist=True) is None:
                    db.execute('COMMIT')
                    return False
                db.execute('INSERT INTO iam_revocations VALUES (?,?)',(revision+1,session_id))
                new_pin = self._state(db,self._root,self._domain)[3]
                db.execute('COMMIT')
                self._pin = new_pin
                return True
        except (ValueError,sqlite3.Error,OSError):
            return False


@dataclass(frozen=True)
class SessionClaimCheck:
    """D0 server-owned exact session check; no ORG grant or D4 approval."""
    resolver: D0SessionResolver = field(repr=False)
    credential: str = field(repr=False)
    observation: SessionObservation
    scope: tuple[str,str,str]
    principal: str
    agent: str

    def inspect(self, authority, db):
        if (type(self.resolver) is not D0SessionResolver or self.resolver._authority is not authority
                or type(self.observation) is not SessionObservation):
            raise ValueError('IAM_CLAIM_HOLD')
        actual = self.resolver._read_durable(db,self.credential,self.scope,persist_clock=False)
        if (actual is None or actual != self.observation or actual.kind != 'AGENT'
                or actual.principal_id != self.principal or actual.agent_instance_id != self.agent):
            raise ValueError('IAM_CLAIM_HOLD')
        return sha256(json.dumps(['d5-g2-session-claim',self.resolver._pin,asdict(actual)],
                      sort_keys=True,separators=(',',':')).encode('ascii')).hexdigest()
