"""Deterministic ORG-10 fixture derivation. Never connects to a database.
Original R4/R5 sources remain untouched; outputs must go to a NEW directory.
Port and roles are proposed for owner review, not reserved or authorized.
"""
from pathlib import Path
import argparse, hashlib, json, re

PINS = {
    'ORG-05R4/PG_SCHEMA_R4.sql': 'f5ebb556ccc9b37a0f2bd0e05f36c7cf85a5bd54de9c1d0244845f146f7b3731',
    'ORG-05R5/bootstrap_roles.sql': '57bf261f759ff7e0adfcae5c81c6755e4124f72908ce99498d1bbc1e4b8d6479',
    'ORG-05R5/pg_transaction.py': '62217451cb83f9aab039c48976b4ab135f1826160156b93781fecab9e900e338',
    'ORG-05R5/pg_operations.py': '65493c2c025260ec8a521254e6ec3d6d9e7b8c0a66210222dc415b3c082028b5',
    'ORG-05R5/run_pg_acceptance.py': 'f4200be09bb0381c4e227b37028e22be7743b815d5c23f9ed155ec794cb1b784',
    'ORG-05R5/test_pg_protocol.py': 'c4a47bac9d95d27269029931899305809c71dbc5d5410af6476a05f37a810d5a',
}
PORT=55436
SCOPE=('synthetic-tenant','synthetic-company','A0_SAMPLE_ONLY')
CONTROL=('synthetic-tenant-org10-control','synthetic-company-org10-control','A0_SAMPLE_ONLY')
SCHEMA='aicos_org10_fixture'
DATABASE=CLUSTER='aicos_org10_disposable'
ROLES=tuple('aicos_org10_'+x for x in ('owner','writer_a','writer_b','reader_a','unmapped'))
TABLES=tuple('org_revision org_head org_unit org_position org_definition_ref org_instance_ref org_binding org_notice op_team op_member op_entry op_notice'.split())
OLD_SHA=PINS['ORG-05R4/PG_SCHEMA_R4.sql']


def sha(raw): return hashlib.sha256(raw).hexdigest()


def exact(text, old, new, count=1):
    if text.count(old)!=count: raise ValueError('DERIVATION_TARGET_HOLD')
    return text.replace(old,new)


def names(text):
    # Literal profile substitution only, no mapping of live data/credentials.
    for old,new in [('aicos_org_r5_disposable',CLUSTER),('aicos_org_r4_disposable',DATABASE),
                    ('aicos_org_r4_', 'aicos_org10_'),('synthetic-tenant-a',SCOPE[0]),
                    ('synthetic-company-a',SCOPE[1]),('synthetic-tenant-b',CONTROL[0]),
                    ('synthetic-company-b',CONTROL[1]),('ORG_R4_SAMPLE_ONLY',SCOPE[2])]:
        text=text.replace(old,new)
    return text


def source(root):
    result={}
    for p,pin in PINS.items():
        raw=(Path(root)/'candidates'/p).read_bytes()
        if sha(raw)!=pin: raise ValueError('ORIGINAL_SOURCE_PIN_HOLD: '+p)
        result[Path(p).name]=raw.decode('utf-8')
    return result


def derive(original):
    out={}
    ddl=names(original['PG_SCHEMA_R4.sql'])
    ddl=exact(ddl,'-- ORG-05R4: disposable PostgreSQL 17 candidate; NOT_RUN; DO NOT APPLY to product.',
        '-- ORG-10: proposed common-scope PostgreSQL 17 fixture; NOT_RUN; DO NOT APPLY to product.')
    ddl=exact(ddl,"IF current_database() <> 'aicos_org10_disposable' OR current_user <> session_user",
        "IF current_database() <> 'aicos_org10_disposable' OR current_setting('cluster_name') <> 'aicos_org10_disposable' OR current_setting('port') <> '55436' OR current_setting('server_version_num')::integer NOT BETWEEN 170000 AND 179999 OR current_user <> 'org10_admin' OR host(inet_server_addr()) IS DISTINCT FROM '127.0.0.1' OR host(inet_client_addr()) IS DISTINCT FROM '127.0.0.1' OR current_user <> session_user")
    ddl=ddl.replace('ORG_R4_DISPOSABLE_ADMIN_REQUIRED','ORG10_DISPOSABLE_ADMIN_REQUIRED').replace('ORG_R4_OWNER_REQUIRED','ORG10_OWNER_REQUIRED').replace('ORG_R4_ROLE_BOUNDARY','ORG10_ROLE_BOUNDARY')
    out['PG_SCHEMA_ORG10.sql']=ddl
    boot=names(original['bootstrap_roles.sql'])
    boot=exact(boot,'-- ORG-05R5 isolated test setup ONLY. PostgreSQL 17, fresh local cluster.', '-- ORG-10 proposed isolated test setup ONLY. PostgreSQL 17, fresh separate local cluster.')
    boot=exact(boot,"OR current_user<>session_user OR NOT EXISTS", "OR current_setting('port')<>'55436' OR current_user<>'org10_admin'\n    OR current_user<>session_user OR NOT EXISTS")
    boot=exact(boot,"OR (inet_server_addr() IS NOT NULL AND host(inet_server_addr()) NOT IN ('127.0.0.1','::1'))", "OR host(inet_server_addr()) IS DISTINCT FROM '127.0.0.1'")
    boot=exact(boot,"OR (inet_client_addr() IS NOT NULL AND host(inet_client_addr()) NOT IN ('127.0.0.1','::1'))", "OR host(inet_client_addr()) IS DISTINCT FROM '127.0.0.1'")
    boot=exact(boot,"OR EXISTS(SELECT 1 FROM pg_catalog.pg_roles WHERE rolname LIKE 'aicos_org10_%')", "OR EXISTS(SELECT 1 FROM pg_catalog.pg_roles WHERE rolname<>current_user AND left(rolname,3)<>'pg_')")
    boot=exact(boot,'ORG_R5_FRESH_DISPOSABLE_ADMIN_REQUIRED','ORG10_FRESH_DISPOSABLE_ADMIN_REQUIRED')
    out['bootstrap_roles.sql']=boot
    tx=names(original['pg_transaction.py'])
    tx=exact(tx,'"""ORG-05R5 disposable PG transaction boundary. No production authority."""','"""ORG-10 derived R5 fixture transaction boundary; no production authority."""')
    tx=exact(tx,"CLUSTER = 'aicos_org10_disposable'", "CLUSTER = 'aicos_org10_disposable'\nPORT = 55436")
    tx=exact(tx,"current_setting('server_version_num') FROM", "current_setting('server_version_num'), current_setting('port') FROM")
    tx=exact(tx,'len(row)==15','len(row)==16')
    tx=exact(tx,"row[9] in (None,'127.0.0.1','::1') and row[10] in (None,'127.0.0.1','::1')", "row[9] in ('127.0.0.1','::1') and row[10] in ('127.0.0.1','::1')")
    tx=exact(tx,"'PG_CLUSTER_VERSION')\n", "'PG_CLUSTER_VERSION')\n    require(row[15]==str(PORT), 'PG_PORT')\n")
    out['pg_transaction.py']=tx
    # Identical operation logic; imports resolve only within this isolated candidate.
    out['pg_operations.py']=original['pg_operations.py']
    test=names(original['test_pg_protocol.py'])
    test=exact(test,"CLUSTER,'170012')", "CLUSTER,'170012','55436')")
    test=exact(test,"'core','170012')", "'core','170012','55436')")
    test=exact(test,"'180004')", "'180004',d.row[15])")
    out['test_pg_protocol.py']=test
    runner=names(original['run_pg_acceptance.py'])
    runner=exact(runner,'Explicit opt-in, fresh R4 disposable PG fixture.', 'Explicit opt-in, fresh ORG-10 proposed common-scope disposable PG fixture.')
    runner=exact(runner,'Requires exact R3 modules, R4 schema installed, reviewed local credentials; no DDL here.', 'Requires exact R3 modules, reviewed ORG-10 schema and separate local credentials; no DDL here.')
    runner=exact(runner,"R4 = Path(__file__).resolve().parent.parent/'ORG-05R4'", "R4 = Path(__file__).resolve().parent")
    runner=exact(runner,"R4/'PG_SCHEMA_R4.sql'", "R4/'PG_SCHEMA_ORG10.sql'")
    runner=exact(runner,OLD_SHA,sha(ddl.encode()),2)
    runner=exact(runner,'def verify_sources():\n', "def verify_sources():\n    from derive_common import source, derive, verify_generated\n    verify_generated(Path(__file__).resolve().parent, derive(source(Path(__file__).resolve().parents[2])))\n")
    runner=exact(runner,'not 1<=args.port<=65535','args.port!=55436')
    runner=exact(runner,'import psycopg\n',"import psycopg\n    import importlib.metadata as metadata\n    if (metadata.version('psycopg')!='3.3.9' or metadata.version('psycopg-binary')!='3.3.9' or psycopg.pq.__impl__!='binary'):\n        raise Hold('DRIVER_PIN_HOLD')\n")
    runner=exact(runner,"'ORG-05R5_DISPOSABLE_ONLY'","'ORG10_COMMON_SCOPE_DISPOSABLE_ONLY'")
    runner=exact(runner,"        check('PG26_FINAL_COUNTS',lambda:eq(counts(),(2,2)))\n", """        check('PG26_FINAL_COUNTS',lambda:eq(counts(),(2,2)))
        check('PG27_TENANT_ONLY',lambda:denied(lambda:foreign_insert((sb[0],sa[1],sa[2])),'42501'))
        check('PG28_OLD_SCOPE_A',lambda:denied(lambda:foreign_insert(('synthetic-tenant-a','synthetic-company-a','ORG_R4_SAMPLE_ONLY')),'42501'))
        check('PG29_OLD_SCOPE_B',lambda:denied(lambda:foreign_insert(('synthetic-tenant-b','synthetic-company-b','ORG_R4_SAMPLE_ONLY')),'42501'))
        def reverse_scope_read():
            for t in sorted(TABLES):
                sql=f'SELECT count(*) FROM {SCHEMA}.{t} WHERE t=%s AND c=%s AND e=%s'
                own=query(fa,sa,sql,sa)[0][0]
                if own<=0: raise AssertionError('VACUOUS_SCOPE_PROBE')
                eq(query(fr,sa,sql,sa),[(own,)])
                eq(query(fb,sb,sql,sa),[(0,)])
            return {'tables':len(TABLES),'reader_matches':True,'other_scope_hidden':True}
        check('PG30_REVERSE_SCOPE_READ',reverse_scope_read)
        def acl_matrix():
            def inspect(db):
                def acl(sql,params): return db.execute(sql,params).fetchall()
                for t in sorted(TABLES):
                    for role in roles:
                        permitted=role in roles[:3]; writer=role in roles[:2]
                        for privilege, expected in (('SELECT',permitted),('INSERT',writer),('UPDATE',False),('DELETE',False),('TRUNCATE',False),('REFERENCES',False),('TRIGGER',False)):
                            eq(acl('SELECT pg_catalog.has_table_privilege(%s,%s,%s)',(role,f'{SCHEMA}.{t}',privilege)),[(expected,)])
                        if t=='org_head':
                            for col in ('t','c','e','rev'):
                                eq(acl('SELECT pg_catalog.has_column_privilege(%s,%s,%s,%s)',(role,f'{SCHEMA}.{t}',col,'UPDATE')),[(writer and col=='rev',)])
                for role in roles:
                    eq(acl('SELECT pg_catalog.has_database_privilege(%s,%s,%s)',(role,DATABASE,'CONNECT')),[(True,)])
                    eq(acl('SELECT pg_catalog.has_database_privilege(%s,%s,%s)',(role,DATABASE,'TEMP')),[(False,)])
                return {'tables':len(TABLES),'roles':len(roles),'checks':len(TABLES)*len(roles)*7+len(roles)*4+len(roles)*2}
            return run(fa,sa,False,inspect)
        check('PG31_ACL_MATRIX',acl_matrix)
""")
    out['run_pg_acceptance.py']=runner
    return {n:s.encode('utf-8') for n,s in out.items()}


def verify_generated(directory, data):
    for name,raw in data.items():
        if (Path(directory)/name).read_bytes()!=raw:
            raise ValueError('GENERATED_SOURCE_HOLD: '+name)
    return len(data)


def main():
    p=argparse.ArgumentParser(); p.add_argument('--source-root',required=True,type=Path)
    group=p.add_mutually_exclusive_group(required=True)
    group.add_argument('--output',type=Path); group.add_argument('--verify',type=Path)
    a=p.parse_args(); data=derive(source(a.source_root))
    if a.verify:
        print('EXACT_GENERATED_PASS',verify_generated(a.verify,data)); return
    a.output.mkdir(parents=False,exist_ok=False)
    for n,b in data.items():
        with (a.output/n).open('xb') as f:f.write(b)
    print(json.dumps({n:sha(b) for n,b in data.items()},indent=2))

if __name__=='__main__':main()
