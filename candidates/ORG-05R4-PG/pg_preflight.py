"""ORG-05R4: deterministic D0 PostgreSQL fixture generator. Never connects or executes SQL."""
from contextlib import closing
from hashlib import sha256
from pathlib import Path
import argparse
import json
import re
import sqlite3

ROOT = Path(__file__).resolve().parent
PINS = {
    'schema.sql': '76e71112695ade87fd55a63cbd156ca8eb14f96f0971a3883735aa0ecc21d3ed',
    'operations.sql': '97c595a2e11b1822bf5ca1bda70417915503fdb14f29866927979cf044fd6a77',
}
TABLES = ('org_revision','org_head','org_unit','org_position','org_definition_ref',
          'org_instance_ref','org_binding','org_notice','op_team','op_member','op_entry','op_notice')
SCHEMA = 'aicos_org_r4'
DATABASE = 'aicos_org_r4_fixture'
OWNER = 'aicos_org_r4_owner'
UNMAPPED = 'aicos_org_r4_unmapped'
# Independent changes to tenant, company, environment; reader shares A's scope.
WRITERS = {
    'aicos_org_r4_a': ('synthetic-tenant-a','synthetic-company-a','A0_SAMPLE_ONLY'),
    'aicos_org_r4_t': ('synthetic-tenant-b','synthetic-company-a','A0_SAMPLE_ONLY'),
    'aicos_org_r4_c': ('synthetic-tenant-a','synthetic-company-b','A0_SAMPLE_ONLY'),
    'aicos_org_r4_e': ('synthetic-tenant-a','synthetic-company-a','A0_REVIEW_ONLY'),
}
READER = 'aicos_org_r4_reader'
READERS = {**WRITERS, READER: WRITERS['aicos_org_r4_a']}
ROLES = (OWNER, UNMAPPED, *READERS)


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def load(root=ROOT/'reference'):
    result = []
    for name, expected in PINS.items():
        p = Path(root)/name
        require(p.is_file() and not p.is_symlink(), 'REFERENCE_MISSING: '+name)
        raw = p.read_bytes()
        require(sha256(raw).hexdigest() == expected, 'SOURCE_PIN_HOLD: '+name)
        result.append(raw.decode('utf-8'))
    return tuple(result)


def inventory(sources):
    """Real SQLite parser/introspection of the exact parent schema; not PG validation."""
    with closing(sqlite3.connect(':memory:')) as db:
        for source in sources:
            db.executescript(source)
        names = tuple(x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
        require(set(names) == set(TABLES), 'TABLE_SCOPE_HOLD')
        out = {}
        for name in TABLES:
            columns = db.execute(f'PRAGMA table_info({name})').fetchall()
            pk = [r[1] for r in sorted((r for r in columns if r[5]),key=lambda r:r[5])]
            require(pk[:3] == ['t','c','e'], 'PK_SCOPE_HOLD: '+name)
            require(all(r[3] for r in columns if r[1] in ('t','c','e')), 'NULL_SCOPE_HOLD: '+name)
            groups = {}
            for r in db.execute(f'PRAGMA foreign_key_list({name})'):
                groups.setdefault(r[0],[]).append(r)
            fks = []
            for rows in groups.values():
                rows.sort(key=lambda r:r[1]); target = rows[0][2]
                lhs, rhs = [r[3] for r in rows],[r[4] for r in rows]
                require(target in TABLES and lhs[:3] == rhs[:3] == ['t','c','e'], 'FK_SCOPE_HOLD: '+name)
                fks.append({'target':target,'from':lhs,'to':rhs})
            unique = []
            for idx in db.execute(f'PRAGMA index_list({name})'):
                if idx[2]:
                    cols = [r[2] for r in db.execute(f'PRAGMA index_info({idx[1]})')]
                    require(cols[:3] == ['t','c','e'], 'UNIQUE_SCOPE_HOLD: '+name)
                    unique.append(cols)
            out[name] = {'pk':pk,'foreign_keys':fks,'unique':unique,
                         'runtime_update':['rev'] if name=='org_head' else [],
                         'runtime_delete':False,'reader_write':False}
        return out


def predicate(mapping):
    parts = [f"(session_user = '{role}' AND (t,c,e) = ('{t}','{c}','{e}'))" for role,(t,c,e) in mapping.items()]
    return '(current_user = session_user AND ('+' OR '.join(parts)+'))'


def render(sources):
    require(tuple(sha256(s.encode('utf-8')).hexdigest() for s in sources) == tuple(PINS.values()), 'SOURCE_PIN_HOLD')
    inv = inventory(sources)
    # Only pinned statements translated; no arbitrary caller SQL or identifier inputs.
    sql = '\n'.join(sources)
    sql = re.sub(r'^--.*\n|^PRAGMA foreign_keys=ON;\n','',sql,flags=re.M)
    sql = re.sub(r'\b(CREATE TABLE|REFERENCES) ([a-z_]+)',lambda m:f'{m[1]} {SCHEMA}.{m[2]}',sql)
    sql = sql.replace(' INTEGER ', ' BIGINT ').replace(') STRICT;',');')
    require('PRAGMA' not in sql and 'STRICT;' not in sql, 'TRANSLATION_HOLD')
    for name in TABLES:
        require(sql.count(f'CREATE TABLE {SCHEMA}.{name}(')+sql.count(f'CREATE TABLE {SCHEMA}.{name} (')==1,'DDL_SCOPE_HOLD')
    role_list = ', '.join("'"+r+"'" for r in ROLES)
    # The reviewed future bootstrap owns creation, LOGIN transitions and credentials.
    lines = ['-- ORG-05R4 disposable fixture candidate; NOT RUN. DO NOT APPLY to product.',
             'BEGIN;',
             f"DO $$ BEGIN IF current_database() <> '{DATABASE}' THEN RAISE EXCEPTION 'ORG_FIXTURE_DATABASE_HOLD'; END IF;",
             f"IF (SELECT count(*) FROM pg_roles WHERE rolname IN ({role_list}) AND NOT rolcanlogin AND NOT rolsuper AND NOT rolbypassrls AND NOT rolcreatedb AND NOT rolcreaterole AND NOT rolreplication AND NOT rolinherit) <> {len(ROLES)} THEN RAISE EXCEPTION 'ORG_ROLE_FLAGS_HOLD'; END IF;",
             f"IF EXISTS (SELECT 1 FROM pg_auth_members m JOIN pg_roles r ON r.oid=m.roleid OR r.oid=m.member WHERE r.rolname IN ({role_list})) THEN RAISE EXCEPTION 'ORG_ROLE_MEMBERSHIP_HOLD'; END IF;",
             f"IF (SELECT pg_get_userbyid(datdba) FROM pg_database WHERE datname=current_database()) <> '{OWNER}' THEN RAISE EXCEPTION 'ORG_DATABASE_OWNER_HOLD'; END IF; END $$;",
             f'CREATE SCHEMA {SCHEMA} AUTHORIZATION {OWNER};', f'SET LOCAL ROLE {OWNER};',
             f'REVOKE ALL ON SCHEMA {SCHEMA} FROM PUBLIC;',
             f'GRANT USAGE ON SCHEMA {SCHEMA} TO '+', '.join((*READERS,UNMAPPED))+';', sql.rstrip()]
    readers, writers = ', '.join(READERS), ', '.join(WRITERS)
    for name in inv:
        q = f'{SCHEMA}.{name}'
        lines += [f'ALTER TABLE {q} ENABLE ROW LEVEL SECURITY;',f'ALTER TABLE {q} FORCE ROW LEVEL SECURITY;',
                  f'REVOKE ALL ON TABLE {q} FROM PUBLIC;',
                  f'CREATE POLICY org_select ON {q} FOR SELECT TO {readers} USING ({predicate(READERS)});',
                  f'CREATE POLICY org_insert ON {q} FOR INSERT TO {writers} WITH CHECK ({predicate(WRITERS)});',
                  f'GRANT SELECT ON TABLE {q} TO {readers}, {UNMAPPED};',
                  f'GRANT INSERT ON TABLE {q} TO {writers};']
        if name=='org_head':
            lines += [f'CREATE POLICY org_update ON {q} FOR UPDATE TO {writers} USING ({predicate(WRITERS)}) WITH CHECK ({predicate(WRITERS)});',
                      f'GRANT UPDATE (rev) ON TABLE {q} TO {writers};']
    lines += ['COMMIT;','']
    return '\n'.join(lines), inv


def generate(dest):
    sources = load()
    ddl, inv = render(sources)
    dest = Path(dest)
    dest.mkdir(parents=True,exist_ok=False)
    (dest/'org_fixture_candidate.sql').write_bytes(ddl.encode('utf-8'))
    report = {'status':'D0_GENERATED_NOT_RUN','database':DATABASE,'schema':SCHEMA,
              'reference_sha256':PINS,'tables':inv,'roles':list(ROLES),'scope_profiles':READERS,
              'sql_sha256':sha256(ddl.encode('utf-8')).hexdigest(),'pg':'NOT_RUN',
              'canonical_rls':'HOLD','identity_owner':'HOLD','dispatch_allowed':False}
    (dest/'PREFLIGHT_REPORT.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    return report


if __name__=='__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',required=True,type=Path)
    print(json.dumps(generate(p.parse_args().output),indent=2))
