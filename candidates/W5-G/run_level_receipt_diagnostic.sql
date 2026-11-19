-- W5-G D0 owner-side diagnostic. No receipt issuance, grant or execution authority.
-- PostgreSQL named parameters; one SELECT; caller owns the scoped read session.
-- An empty result is HOLD. A matching run is still NOT invocation membership.
SELECT 'HOLD' AS decision,
       FALSE AS provider_call_allowed,
       FALSE AS spend_allowed,
       FALSE AS receipt_available,
       CASE
         WHEN a.run_id IS NULL THEN 'ADMISSION_MISSING_HOLD'
         WHEN r.run_id IS NULL THEN 'RESERVATION_MISSING_HOLD'
         WHEN a.budget_id <> %(budget_id)s OR r.budget_id <> a.budget_id
           OR r.transaction_ref <> a.transaction_ref OR r.request_digest <> a.request_digest
           THEN 'RUN_RESERVATION_LINK_HOLD'
         WHEN b.budget_id IS NULL THEN 'BUDGET_MISSING_HOLD'
         WHEN b.unknown_cost THEN 'UNKNOWN_COST_HOLD'
         WHEN b.policy_epoch <> %(policy_epoch)s OR b.witness_epoch <> %(witness_epoch)s
           THEN 'BUDGET_EPOCH_HOLD'
         WHEN b.currency <> r.currency OR b.currency <> %(currency)s
           OR b.revision < r.budget_revision OR r.budget_revision <= 0
           THEN 'BUDGET_REFERENCE_HOLD'
         WHEN s.run_id IS NOT NULL THEN 'RUN_SETTLEMENT_NOT_USAGE_HOLD'
         WHEN r.amount_minor > b.outstanding_minor
           OR b.outstanding_minor > b.limit_minor - b.recognized_cost_minor
           THEN 'BUDGET_BALANCE_HOLD'
         ELSE 'RUN_LEVEL_ONLY_INVOCATION_MEMBERSHIP_MISSING_HOLD'
       END AS reason
FROM t1_candidate.run_heads h
LEFT JOIN t1_candidate.run_admissions a USING (tenant_id,company_id,environment_id,run_id)
LEFT JOIN t1_candidate.sample_reservations r USING (tenant_id,company_id,environment_id,run_id)
LEFT JOIN t1_candidate.sample_budgets b
  ON b.tenant_id=h.tenant_id AND b.company_id=h.company_id
 AND b.environment_id=h.environment_id AND b.budget_id=r.budget_id
LEFT JOIN t1_candidate.sample_settlements s
  ON s.tenant_id=h.tenant_id AND s.company_id=h.company_id
 AND s.environment_id=h.environment_id AND s.run_id=h.run_id
WHERE h.tenant_id='synthetic-tenant' AND h.company_id='synthetic-company'
  AND h.environment_id='A0_SAMPLE_ONLY'
  AND h.tenant_id=%(tenant_id)s AND h.company_id=%(company_id)s
  AND h.environment_id=%(environment_id)s AND h.run_id=%(run_id)s
  AND h.plan_revision=%(plan_revision)s AND h.task_id=%(task_id)s
  AND h.agent_instance_id=%(agent_instance_id)s AND h.principal_id=%(principal_id)s
  AND h.attempt=%(attempt)s;
