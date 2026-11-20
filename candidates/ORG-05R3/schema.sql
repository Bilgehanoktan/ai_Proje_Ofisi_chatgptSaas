-- ORG-05R2 SQLite D0 lab only; NOT a PostgreSQL migration or an authorization schema.
PRAGMA foreign_keys=ON;
CREATE TABLE org_revision (
 t TEXT NOT NULL, c TEXT NOT NULL, e TEXT NOT NULL, rev TEXT NOT NULL,
 seq INTEGER NOT NULL CHECK(seq>0), prev TEXT, staffing_digest TEXT NOT NULL,
 prev_staffing TEXT, PRIMARY KEY(t,c,e,rev), UNIQUE(t,c,e,seq),
 FOREIGN KEY(t,c,e,prev) REFERENCES org_revision(t,c,e,rev),
 CHECK((seq=1 AND prev IS NULL AND prev_staffing IS NULL) OR (seq>1 AND prev IS NOT NULL AND prev_staffing IS NOT NULL))
) STRICT;
CREATE TABLE org_head (
 t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,rev TEXT NOT NULL,
 PRIMARY KEY(t,c,e), FOREIGN KEY(t,c,e,rev) REFERENCES org_revision(t,c,e,rev)
) STRICT;
CREATE TABLE org_unit (
 t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,rev TEXT NOT NULL,id TEXT NOT NULL,
 kind TEXT NOT NULL CHECK(kind IN ('company','division','department','team')),parent TEXT,
 PRIMARY KEY(t,c,e,rev,id), FOREIGN KEY(t,c,e,rev) REFERENCES org_revision(t,c,e,rev),
 FOREIGN KEY(t,c,e,rev,parent) REFERENCES org_unit(t,c,e,rev,id) DEFERRABLE INITIALLY DEFERRED
) STRICT;
CREATE TABLE org_position (
 t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,rev TEXT NOT NULL,id TEXT NOT NULL,
 unit TEXT NOT NULL,role TEXT NOT NULL,manager TEXT,
 PRIMARY KEY(t,c,e,rev,id), UNIQUE(t,c,e,rev,id,role),
 FOREIGN KEY(t,c,e,rev,unit) REFERENCES org_unit(t,c,e,rev,id),
 FOREIGN KEY(t,c,e,rev,manager) REFERENCES org_position(t,c,e,rev,id) DEFERRABLE INITIALLY DEFERRED
) STRICT;
CREATE TABLE org_definition_ref (
 t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,rev TEXT NOT NULL,id TEXT NOT NULL,role TEXT NOT NULL,
 PRIMARY KEY(t,c,e,rev,id), UNIQUE(t,c,e,rev,id,role),
 FOREIGN KEY(t,c,e,rev) REFERENCES org_revision(t,c,e,rev)
) STRICT;
CREATE TABLE org_instance_ref (
 t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,rev TEXT NOT NULL,id TEXT NOT NULL,definition TEXT NOT NULL,role TEXT NOT NULL,
 PRIMARY KEY(t,c,e,rev,id), UNIQUE(t,c,e,rev,id,role),
 FOREIGN KEY(t,c,e,rev,definition,role) REFERENCES org_definition_ref(t,c,e,rev,id,role)
) STRICT;
CREATE TABLE org_binding (
 t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,rev TEXT NOT NULL,seat TEXT NOT NULL,instance TEXT NOT NULL,role TEXT NOT NULL,
 PRIMARY KEY(t,c,e,rev,seat), UNIQUE(t,c,e,rev,instance),
 FOREIGN KEY(t,c,e,rev,seat,role) REFERENCES org_position(t,c,e,rev,id,role),
 FOREIGN KEY(t,c,e,rev,instance,role) REFERENCES org_instance_ref(t,c,e,rev,id,role)
) STRICT;
CREATE TABLE org_notice (
 t TEXT NOT NULL,c TEXT NOT NULL,e TEXT NOT NULL,rev TEXT NOT NULL,
 digest TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind='ORG_REVISION_RECORDED_D0'),
 state TEXT NOT NULL CHECK(state='HOLD'), PRIMARY KEY(t,c,e,rev),
 FOREIGN KEY(t,c,e,rev) REFERENCES org_revision(t,c,e,rev)
) STRICT;
