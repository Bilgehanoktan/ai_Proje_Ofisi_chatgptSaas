-- ORG-10 proposed isolated test setup ONLY. PostgreSQL 17, fresh separate local cluster.
-- Use psql -X -v ON_ERROR_STOP=1 -d postgres as separate cluster administrator.
\set ON_ERROR_STOP on
DO $guard$
BEGIN
 IF current_database()<>'postgres' OR current_setting('cluster_name')<>'aicos_org10_disposable'
    OR current_setting('server_version_num')::integer NOT BETWEEN 170000 AND 179999
    OR current_setting('port')<>'55436' OR current_user<>'org10_admin'
    OR current_user<>session_user OR NOT EXISTS(SELECT 1 FROM pg_catalog.pg_roles WHERE rolname=current_user AND rolsuper)
    OR host(inet_server_addr()) IS DISTINCT FROM '127.0.0.1'
    OR host(inet_client_addr()) IS DISTINCT FROM '127.0.0.1'
    OR EXISTS(SELECT 1 FROM pg_catalog.pg_database WHERE datname NOT IN ('postgres','template0','template1'))
    OR EXISTS(SELECT 1 FROM pg_catalog.pg_roles WHERE rolname<>current_user AND left(rolname,3)<>'pg_')
 THEN RAISE EXCEPTION 'ORG10_FRESH_DISPOSABLE_ADMIN_REQUIRED'; END IF;
END $guard$;
BEGIN;
CREATE ROLE aicos_org10_owner NOLOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION NOINHERIT;
CREATE ROLE aicos_org10_writer_a LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION NOINHERIT;
CREATE ROLE aicos_org10_writer_b LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION NOINHERIT;
CREATE ROLE aicos_org10_reader_a LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION NOINHERIT;
CREATE ROLE aicos_org10_unmapped LOGIN NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE NOREPLICATION NOINHERIT;
SET LOCAL password_encryption='scram-sha-256';
\password aicos_org10_writer_a
\password aicos_org10_writer_b
\password aicos_org10_reader_a
\password aicos_org10_unmapped
COMMIT;
CREATE DATABASE aicos_org10_disposable OWNER aicos_org10_owner;
REVOKE CONNECT,TEMPORARY ON DATABASE aicos_org10_disposable FROM PUBLIC;
GRANT CONNECT ON DATABASE aicos_org10_disposable TO aicos_org10_writer_a,aicos_org10_writer_b,aicos_org10_reader_a,aicos_org10_unmapped;
