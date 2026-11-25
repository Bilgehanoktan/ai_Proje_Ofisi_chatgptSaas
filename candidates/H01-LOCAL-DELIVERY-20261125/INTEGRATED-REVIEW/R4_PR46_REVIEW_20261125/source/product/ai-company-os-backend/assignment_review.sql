-- Additive D0 owner-review candidate. Fresh disposable SQLite only; no grants.
CREATE TABLE op_assignment_review (
 t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,run TEXT NOT NULL,
 revision INTEGER NOT NULL CHECK(revision IN (1,2)),
 state TEXT NOT NULL CHECK((revision=1 AND state='ACCEPTED_D0') OR (revision=2 AND state='REVOKED_D0')),
 previous TEXT NOT NULL CHECK(length(previous)=64), digest TEXT NOT NULL CHECK(length(digest)=64), body TEXT NOT NULL,
 PRIMARY KEY(t,c,e,run,revision), UNIQUE(t,c,e,digest)
) STRICT;
CREATE TRIGGER op_assignment_review_no_update BEFORE UPDATE ON op_assignment_review
 BEGIN SELECT RAISE(ABORT,'IMMUTABLE'); END;
CREATE TRIGGER op_assignment_review_no_delete BEFORE DELETE ON op_assignment_review
 BEGIN SELECT RAISE(ABORT,'IMMUTABLE'); END;
