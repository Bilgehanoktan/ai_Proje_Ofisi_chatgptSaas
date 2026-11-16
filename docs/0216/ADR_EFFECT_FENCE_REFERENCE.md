# ADR-0216 — D0 reference before mandatory gateway wiring
Status: engineering choice, not normative ratification or independent acceptance.
Context: 0215 read-only signed observation cannot authorize effects; original 0211 authority is local and restore-vulnerable.
Decision: add isolated synthetic consume/head reference and tests under product; no new live route, no changes to canonical authority, no callbacks, no independent grant. Use SQLite writer serialization to model exact head/claim ordering and permanent uniqueness. Alternative of immediately wiring a new authority to T1/gateways rejected until architecture/security review and independent custody; alternative of declaring signed readback a grant rejected.
Consequences: local useful evidence, known rollback weakness persists. D-01–D-04 OPEN. No canonical API/DB/event/dependency change. Retire or reconcile fixture after independently reviewed protocol; never use as security root.
