-- ORG-05R5 isolated test setup ONLY. PostgreSQL 17, fresh local cluster.
-- Use psql -X -v ON_ERROR_STOP=1 -d postgres as separate cluster administrator.
\set ON_ERROR_STOP on
DO $guard$
BEGIN
 IF current_database()<>'postgres' OR current_setting('cluster_name')<>'aicos_org_r5_disposable'
    OR current_setting('server_version_num')::integer NOT BETWEEN 170000 AND 179999
    OR current_user<>session_user OR NOT EXISTS(SELECT 1 FROM pg_catalog.pg_roles WHERE rolname=current_user AND rolsuper)
    OR (inet_server_addr() IS NOT NULL AND host(inet_server_addr()) NOT IN ('127.0.0.1','::1'))
    OR (inet_client_addr() IS NOT NULL AND host(inet_client_addr()) NOT IN ('127.0.0.1','::1'))
    OR EXISTS(SELECT 1 FROM pg_catalog.pg_database WHERE datname NOT IN ('postgres','template0','template1'))
    OR EXISTS(SELECT 1 FROM pg_catalog.pg_roles WHERE rolname LIKE 'aicos_org_r4_%')
 THEN RAISE EXCEPTION 'ORG_R5_FRESH_DISPOSABLE_ADMIN_REQUIRED'; END IF;
END $guard$;
BEGIN;
CREATE ROLE aicos_org_r4_owner NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION NOINHERIT;
CREATE ROLE aicos_org_r4_writer_a LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION NOINHERIT;
CREATE ROLE aicos_org_r4_writer_b LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION NOINHERIT;
CREATE ROLE aicos_org_r4_reader_a LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION NOINHERIT;
CREATE ROLE aicos_org_r4_unmapped LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION NOINHERIT;
SET LOCAL password_encryption='scram-sha-256';
\password aicos_org_r4_writer_a
\password aicos_org_r4_writer_b
\password aicos_org_r4_reader_a
\password aicos_org_r4_unmapped
COMMIT;
CREATE DATABASE aicos_org_r4_disposable OWNER aicos_org_r4_owner;
REVOKE CONNECT,TEMPORARY ON DATABASE aicos_org_r4_disposable FROM PUBLIC;
GRANT CONNECT ON DATABASE aicos_org_r4_disposable TO aicos_org_r4_writer_a,aicos_org_r4_writer_b,aicos_org_r4_reader_a,aicos_org_r4_unmapped;
