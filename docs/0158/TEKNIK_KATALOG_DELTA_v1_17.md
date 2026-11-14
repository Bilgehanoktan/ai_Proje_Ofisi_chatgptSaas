# Teknik katalog v1.17 — 0158

## CHG-0158-01 — `witness_review.py`
- Semboller: WitnessSample, WitnessReview, valid_witness, inspect_witness, RestoreObservation, RestoreReview, inspect_restore
- Neden/nasıl: D14/D16: reference equality, scope, epoch, age, monotonic sequence; restore stays read-only; UNKNOWN keys require reconciliation
- Teşhis: WA_REFERENCE_MISSING, WA_SCOPE_MISMATCH, ERR_WA_EPOCH_STALE, WA_REFERENCE_MISMATCH, WA_OBSERVATION_NOT_FRESH, RESTORE_MONOTONIC_FENCE_REQUIRED, UNKNOWN_RECONCILIATION_REQUIRED
- Geri dönüş: doğrulanmış R4 ZIP; 5 ek dosya ve manifest birlikte.

## CHG-0158-02 — `policy_gateway_review.py`
- Semboller: EffectScope, GrantSample, GatewayReview, valid_effect, valid_grant, inspect_gateway, DisabledToolGateway.dispatch
- Neden/nasıl: D12/D14: exact grant/effect binding, action/tool intersection, lease and witness freshness, existing deny_effect; no connector or allow branch
- Teşhis: GRANT_REFERENCE_MISMATCH, GRANT_REVOKED, GRANT_EXPIRED, EFFECT_OUTSIDE_GRANT, GATEWAY_LEASE_BINDING_MISMATCH, PEP_ISOLATION_NOT_PROVEN
- Geri dönüş: doğrulanmış R4 ZIP; 5 ek dosya ve manifest birlikte.

## CHG-0158-03 — `iv_review.py`
- Semboller: TrustPlane, ArtifactPin, IVObservation, IVReview, valid_pin, plane_ids, valid_plane, inspect_iv
- Neden/nasıl: D11: separate trust-plane identifiers and artifact/readback/current CAS binding; never verify signature or issue receipt
- Teşhis: IV_TRUST_PLANE_COLLISION, IV_ARTIFACT_READBACK_CAS_MISMATCH, IV_TRUST_ROOT_UNPROVEN
- Geri dönüş: doğrulanmış R4 ZIP; 5 ek dosya ve manifest birlikte.

## CHG-0158-04 — `skill_review.py`
- Semboller: SkillManifestSample, SkillReview, valid_manifest, inspect_skill
- Neden/nasıl: D08: exact manifest/schema pins, scope, unique tools; disabled quarantine; G7/G8 refs not proof
- Teşhis: SKILL_PIN_SCOPE_MISMATCH, SKILL_ENABLE_PROHIBITED, F0_REVIEW_RECEIPT_ABSENT
- Geri dönüş: doğrulanmış R4 ZIP; 5 ek dosya ve manifest birlikte.

## CHG-0158-05 — `test_security_review_0158.py`
- Semboller: SecurityReviewTests (9 methods)
- Neden/nasıl: Offline oracle candidates for deny, stale, revoke, restore, IV and skill; NOT_RUN
- Teşhis: Run only in separately authorized environment; no accepted real evidence
- Geri dönüş: doğrulanmış R4 ZIP; 5 ek dosya ve manifest birlikte.

API, DB, dependency değişmedi. Kaynak hashleri SOURCE_CHANGESET_0158.json.
