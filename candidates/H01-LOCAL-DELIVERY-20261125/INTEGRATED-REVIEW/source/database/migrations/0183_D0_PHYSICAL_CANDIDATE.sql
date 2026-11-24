-- DESIGN ONLY / DO NOT APPLY. R03 owner mapping and independent acceptance HOLD.
-- PostgreSQL isolated D0 candidate, not a canonical T1 migration or production role grant.
BEGIN;
CREATE SCHEMA aicos_d0_candidate;
CREATE TABLE aicos_d0_candidate.head (
 tenant_id text NOT NULL CHECK (tenant_id='synthetic-tenant'),
 company_id text NOT NULL CHECK (company_id='synthetic-company'),
 aggregate_id text NOT NULL, version bigint NOT NULL CHECK (version>=0),
 state text NOT NULL CHECK (state IN ('PENDING','OBSERVED')),
 PRIMARY KEY (tenant_id,company_id,aggregate_id)
);
CREATE TABLE aicos_d0_candidate.lease (
 tenant_id text NOT NULL, company_id text NOT NULL, aggregate_id text NOT NULL,
 holder text NOT NULL, fence bigint NOT NULL CHECK (fence>0),
 heartbeat_tick bigint NOT NULL CHECK (heartbeat_tick>=0), expires_tick bigint NOT NULL,
 CHECK (expires_tick>heartbeat_tick),
 PRIMARY KEY (tenant_id,company_id,aggregate_id),
 FOREIGN KEY (tenant_id,company_id,aggregate_id) REFERENCES aicos_d0_candidate.head
);
CREATE TABLE aicos_d0_candidate.event (
 tenant_id text NOT NULL, company_id text NOT NULL, aggregate_id text NOT NULL,
 command_id text NOT NULL, version bigint NOT NULL CHECK (version>0),
 request_sha text NOT NULL CHECK (request_sha ~ '^[a-f0-9]{64}$'),
 PRIMARY KEY (tenant_id,company_id,command_id),
 UNIQUE (tenant_id,company_id,aggregate_id,version),
 FOREIGN KEY (tenant_id,company_id,aggregate_id) REFERENCES aicos_d0_candidate.head
);
CREATE TABLE aicos_d0_candidate.audit (
 tenant_id text NOT NULL, company_id text NOT NULL, command_id text NOT NULL,
 decision text NOT NULL CHECK (decision='SAMPLE_ONLY'),
 PRIMARY KEY (tenant_id,company_id,command_id),
 FOREIGN KEY (tenant_id,company_id,command_id) REFERENCES aicos_d0_candidate.event
);
CREATE TABLE aicos_d0_candidate.outbox (
 tenant_id text NOT NULL, company_id text NOT NULL, command_id text NOT NULL,
 status text NOT NULL CHECK (status='DENY'),
 PRIMARY KEY (tenant_id,company_id,command_id),
 FOREIGN KEY (tenant_id,company_id,command_id) REFERENCES aicos_d0_candidate.event
);
-- No login role, grants, or RLS bypass configured. No effective row policies: fail closed for non-owner roles.
ALTER TABLE aicos_d0_candidate.head ENABLE ROW LEVEL SECURITY;
ALTER TABLE aicos_d0_candidate.head FORCE ROW LEVEL SECURITY;
ALTER TABLE aicos_d0_candidate.lease ENABLE ROW LEVEL SECURITY;
ALTER TABLE aicos_d0_candidate.lease FORCE ROW LEVEL SECURITY;
ALTER TABLE aicos_d0_candidate.event ENABLE ROW LEVEL SECURITY;
ALTER TABLE aicos_d0_candidate.event FORCE ROW LEVEL SECURITY;
ALTER TABLE aicos_d0_candidate.audit ENABLE ROW LEVEL SECURITY;
ALTER TABLE aicos_d0_candidate.audit FORCE ROW LEVEL SECURITY;
ALTER TABLE aicos_d0_candidate.outbox ENABLE ROW LEVEL SECURITY;
ALTER TABLE aicos_d0_candidate.outbox FORCE ROW LEVEL SECURITY;
-- Deliberate rollback: a reviewed, separate migration would be required to apply any DDL.
ROLLBACK;
