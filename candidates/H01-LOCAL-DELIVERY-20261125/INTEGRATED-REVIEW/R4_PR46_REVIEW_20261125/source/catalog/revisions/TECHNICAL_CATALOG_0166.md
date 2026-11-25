# 0166 technical catalog

- coordination_readback.py: classes ReadbackReview; functions inspect_readback, project_readback; imports model, planner, identity_registry, trusted_policy, policy, evidence, trust_boundary, staging_readback
- staging_readback.py: classes StagedRow, ReplayPin, BatchPin, StagingReview; functions expected_rows, batch_digest, inspect_batch; imports dataclasses, hashlib, json, model, planner, evidence, trust_boundary, lifecycle, transaction.review
- trust_boundary.py: classes TrustPin, TrustReview; functions trust_digest, valid_trust, inspect_trust; imports dataclasses, model, planner, identity_registry, trusted_policy, lifecycle, transaction.review
- test_development_review_0166.py: classes ReadbackCandidateTests; functions h, setUp, trust_review, batch_review, coord, test_trust_match_never_authenticates, test_trust_stale, test_trust_future, test_trust_reference, test_trust_wrong_issuer, test_trust_revocation_unknown, test_batch_match_no_authority, test_batch_restore_head, test_batch_replay_sequence, test_batch_policy_mismatch, test_batch_schema_tamper, test_batch_row_missing, test_batch_row_tamper, test_batch_cross_scope_replay, test_coordinator_complete_no_write, test_coordinator_requires_staging, test_projection_never_pass; imports unittest, dataclasses, hashlib, development_review.*

No API, DB, event or dependency version changes. 17 tests NOT_RUN. See JSON, architecture and maintenance.
