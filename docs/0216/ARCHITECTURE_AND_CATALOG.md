# DOC-REV-0216 — isolated D0 synthetic effect-fence reference

Parent branch head `f3b8f0f1ba972c48d13249ed88885cb35900b17f`; source checkpoint `1e01ad5dea65213a86a2401b83fd698436318099`. CEO-0174 and CEO-0179=B permit isolated source integration/tests, not independent acceptance, actual security grants or live effects. 2 product files added; 360 manifest entries / 361 product files including manifest. Exact source readback 2/2; prior 358 manifest records unchanged, not a full byte checkout.

## Architecture and implementation
New `effect_fence_reference.py` deliberately does not replace or call `intent_authority.py`, `external_claim_review.py`, `fenced_transition.py`, T1 or gateways. Separate disposable SQLite fixture only. Head CAS requires seq+1 and nondecreasing recovery epoch, exact expected root. BEGIN IMMEDIATE serializes consume and advance; uniqueness covers scope, binding and transaction reference. Synthetic receipt is the consumed row, not an external effect or release receipt. No callback, actual provider, network or external execution. All external effect decisions HOLD. No canonical schema/API/event/dependency change. Existing signed readback stays diagnostic. See ADR.

## Evidence
13 actual local unittest cases, 12 expected controls and 1 expected residual reproduction. Separate product DB restore preserves consumed claim; restoring reference DB itself enables replay. This is explicitly NOT independent custody or distributed revocation/effect fencing. The caller-supplied hash/sequence is not an authenticated grant; filesystem control/privileged mutation is outside fixture trust. No concurrent revoke-to-remote-effect or T1 commit test. No 0215 regression rerun. PostgreSQL/initdb/psycopg absent, git checkout DNS blocked, full build/browser NOT_RUN. Gate scope remains 7/16 (43.75%), not global product completion.

## Maintenance and rollback
On stale head or duplicate claim, stop; inspect exact expected head and durable consumed row, never reset or retry an uncertain effect. If store missing, preserve artifacts and HOLD. Use fresh disposable fixture only for new synthetic test; no real data. Revert source changes on isolated development branch; preserve consumed evidence and history, never restore authority to authorize replay. Future independent service requires separate custody, authenticated command, trusted time/head, signed receipts and mandatory reviewed T1/tool/model gateway boundary.

[ADR](ADR_EFFECT_FENCE_REFERENCE.md) · [Catalog](../../catalog/revisions/TECHNICAL_CATALOG_0216.json) · [Evidence](../../releases/GITHUB_READBACK_0216.json) · [Next](../../handover/NEXT_STEP_0216.md).
