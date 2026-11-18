"""Exact-source D0 experiment. Never install generated source in the product."""
from hashlib import sha1
from pathlib import Path
import sys

PIN = 'fa47acd32adb309896f762ec50e47bf26641adbb'
HERE = Path(__file__).resolve().parent


def derive(raw):
    if sha1(b'blob '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest() != PIN:
        raise ValueError('D5E_ORIGINAL_PIN_HOLD')
    src = raw.decode('utf-8')
    def replace(old, new):
        nonlocal src
        if src.count(old) != 1:
            raise ValueError('D5E_PATCH_CONTEXT_HOLD')
        src = src.replace(old, new, 1)
    replace('"""0211 D0 restore-external intent authority fixture; no live effects or trust grant.', '"""D5-E generated D0 publication experiment; no product authority or live effects.')
    replace('\n\ndef _path(path):', '''

@dataclass(frozen=True)
class PublicationPin:
    sequence: int
    root_sequence: int
    owner_sha: str

    def validate(self):
        if (type(self.sequence) is not int or not 0 < self.sequence < 2**63
                or type(self.root_sequence) is not int or not 0 < self.root_sequence < 2**63
                or not _digest(self.owner_sha)):
            raise ValueError('D5E_PUBLICATION_PIN_HOLD')


def _path(path):''')
    replace("        db.execute('PRAGMA trusted_schema=OFF')\n        return db", "        db.execute('PRAGMA trusted_schema=OFF')\n        db.execute('PRAGMA foreign_keys=ON')\n        return db")
    replace('    def create(cls, path, root):\n        if type(root) is not RootPin:', '    def create(cls, path, root, *, owner_sha):\n        if not _digest(owner_sha):\n            raise ValueError(\'D5E_OWNER_PIN_HOLD\')\n        if type(root) is not RootPin:')
    replace("            db.execute('INSERT INTO roots VALUES (1,?,?,?)', (root.record_sha, root.key_sha, root.recovery_epoch))\n            db.execute('COMMIT')", '''            db.execute('INSERT INTO roots VALUES (1,?,?,?)', (root.record_sha, root.key_sha, root.recovery_epoch))
            db.execute('CREATE TABLE publication_versions(seq INTEGER PRIMARY KEY, root_seq INTEGER NOT NULL REFERENCES roots(seq), parent_sha TEXT, owner_sha TEXT NOT NULL UNIQUE)')
            db.execute('CREATE TABLE publication_final(seq INTEGER PRIMARY KEY REFERENCES publication_versions(seq))')
            for table in ('publication_versions','publication_final'):
                for op in ('UPDATE','DELETE'):
                    db.execute(f"CREATE TRIGGER {table}_no_{op.lower()} BEFORE {op} ON {table} BEGIN SELECT RAISE(ABORT,'append only'); END")
                db.execute(f"CREATE TRIGGER {table}_no_replace BEFORE INSERT ON {table} WHEN EXISTS(SELECT 1 FROM {table} WHERE seq=NEW.seq) BEGIN SELECT RAISE(ABORT,'append only'); END")
            db.execute("CREATE TRIGGER publication_versions_no_alias BEFORE INSERT ON publication_versions WHEN EXISTS(SELECT 1 FROM publication_versions WHERE owner_sha=NEW.owner_sha) BEGIN SELECT RAISE(ABORT,'append only'); END")
            db.execute('INSERT INTO publication_versions VALUES (1,1,NULL,?)', (owner_sha,))
            db.execute('INSERT INTO publication_final VALUES (1)')
            db.execute('COMMIT')''')
    start=src.index('    def publish(self, expected, new):')
    end=src.index('    @contextmanager\n    def claim_and_fence', start)
    original_publish=src[start:end]
    replace(original_publish, '''    def publish(self, expected, new):
        # Legacy witness-only publication cannot participate in this experiment.
        # A joint witness evolution contract is not implemented.
        raise ValueError('D5E_LEGACY_PUBLISH_HOLD')

    @staticmethod
    def _publication_state(db, root_seq):
        """Return exact last observation and pending status, not an auth grant."""
        rows = db.execute('SELECT seq,root_seq,parent_sha,owner_sha FROM publication_versions ORDER BY seq').fetchall()
        finals = [r[0] for r in db.execute('SELECT seq FROM publication_final ORDER BY seq')]
        if not rows or not finals:
            raise ValueError('D5E_PUBLICATION_HISTORY_HOLD')
        previous = None
        seen = set()
        for index,(seq,rs,parent,sha) in enumerate(rows,1):
            if (seq != index or rs != root_seq or parent != previous
                    or not _digest(sha) or sha in seen):
                raise ValueError('D5E_PUBLICATION_HISTORY_HOLD')
            previous = sha
            seen.add(sha)
        n = len(rows)
        if finals not in (list(range(1,n+1)),list(range(1,n))):
            raise ValueError('D5E_PUBLICATION_HISTORY_HOLD')
        pin = PublicationPin(n,root_seq,previous)
        pin.validate()
        return pin, len(finals) != n

    def _check_publication(self, db, root_seq, expected_publication, read_owner):
        if type(expected_publication) is not PublicationPin or not callable(read_owner):
            raise ValueError('D5E_PUBLICATION_INPUT_HOLD')
        expected_publication.validate()
        latest,pending = self._publication_state(db,root_seq)
        if pending:
            raise ValueError('D5E_PUBLICATION_PENDING_HOLD')
        if latest != expected_publication:
            raise ValueError('D5E_PUBLICATION_STALE_HOLD')
        if read_owner() != latest.owner_sha:
            raise ValueError('D5E_OWNER_READBACK_HOLD')
        return latest

    def publish_protected(self, expected_root, expected_publication, new_owner_sha, *, apply_change, read_owner):
        """Test-only cooperating publisher. No resume/recovery/real IAM API.

        A durable PENDING version precedes external mutation. No successful
        finalization unless exact observed state matches. The lock is the same
        original SQLite writer boundary, not a distributed commit.
        """
        if (type(expected_root) is not RootPin or not _digest(new_owner_sha)
                or not callable(apply_change) or not callable(read_owner)):
            raise ValueError('D5E_PUBLICATION_INPUT_HOLD')
        expected_root.validate()
        with closing(self._db()) as db:
            db.execute('BEGIN IMMEDIATE')
            root_seq,root = self._head(db)
            if root != expected_root:
                raise ValueError('D5E_ROOT_DRIFT_HOLD')
            old = self._check_publication(db,root_seq,expected_publication,read_owner)
            if db.execute('SELECT 1 FROM publication_versions WHERE owner_sha=?',(new_owner_sha,)).fetchone():
                raise ValueError('D5E_PUBLICATION_ALIAS_HOLD')
            pending = PublicationPin(old.sequence+1,root_seq,new_owner_sha)
            pending.validate()
            db.execute('INSERT INTO publication_versions VALUES (?,?,?,?)', (pending.sequence,root_seq,old.owner_sha,new_owner_sha))
            db.execute('COMMIT')
            # Any failure from this point leaves the durable barrier. A new
            # caller cannot take over, compensate, retry or finalize it.
            db.execute('BEGIN IMMEDIATE')
            if self._head(db) != (root_seq,expected_root) or self._publication_state(db,root_seq) != (pending,True):
                raise ValueError('D5E_PENDING_DRIFT_HOLD')
            if read_owner() != old.owner_sha:
                raise ValueError('D5E_OWNER_READBACK_HOLD')
            apply_change()
            if read_owner() != new_owner_sha:
                raise ValueError('D5E_OWNER_READBACK_HOLD')
            db.execute('INSERT INTO publication_final VALUES (?)',(pending.sequence,))
            db.execute('COMMIT')
        return pending

''')
    replace('    def claim_and_fence(self, expected, scope_sha, binding, tx, request_digest):', '    def claim_and_fence(self, expected, scope_sha, binding, tx, request_digest, *, expected_publication=None, read_owner=None):')
    replace("            if current != expected:\n                raise ValueError('D0_AUTHORITY_ROOT_HOLD')\n            if db.execute('SELECT 1 FROM claims", "            if current != expected:\n                raise ValueError('D0_AUTHORITY_ROOT_HOLD')\n            self._check_publication(db,seq,expected_publication,read_owner)\n            if db.execute('SELECT 1 FROM claims")
    replace("            if self._head(db) != (seq, expected):\n                raise ValueError('D0_AUTHORITY_ROOT_CHANGED_HOLD')\n            try:", "            if self._head(db) != (seq, expected):\n                raise ValueError('D0_AUTHORITY_ROOT_CHANGED_HOLD')\n            self._check_publication(db,seq,expected_publication,read_owner)\n            try:")
    # Explicitly remove the product wrapper from the generated experiment.
    i=src.index('\ndef execute_authority_fenced_transition(')
    src=src[:i]+"\ndef execute_authority_fenced_transition(*args, **kwargs):\n    raise ValueError('D5E_PRODUCT_WRAPPER_DISABLED_HOLD')\n"
    compile(src,'<D5-E fixture>','exec')
    return src.encode('utf-8')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('usage: derive_fixture.py NEW_OUTPUT_FILE')
    output=Path(sys.argv[1])
    # Exclusive output, never overwrite the original or another source.
    with output.open('xb') as f:
        f.write(derive((HERE/'intent_authority.original.py').read_bytes()))
