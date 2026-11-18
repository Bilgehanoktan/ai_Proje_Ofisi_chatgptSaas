"""D5-G1: internal D0 bearer-session lookup, not a grant or live IAM service.
Bootstrap records and clock are trusted server-side inputs; no public issuer.
Process-local revocation is not the protected D5 publisher or restore custody.
"""
from dataclasses import dataclass, field
from hashlib import sha256
from hmac import compare_digest
from threading import RLock
from time import monotonic
import re

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
        with self._lock:
            if (not _demo_id(session_id) or not _tick(expected_revision)
                    or expected_revision != self._revision or session_id not in self._records
                    or session_id in self._revoked or self._revision >= 2**63-1):
                return False
            self._revoked.add(session_id)
            self._revision += 1
            return True
