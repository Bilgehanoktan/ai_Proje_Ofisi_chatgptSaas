# MI04 G2 canonical 553 compatibility candidate (review only)

**Scope:** exact preexisting owner G2 source blobs over the exact canonical 553 product tree `254e0188998d0d245bd8ee4eb901aead02951a66`. The four inputs are 3 previously missing product paths plus the one `intent_authority.py` conflict. G2 owner ref `9ca667e816dac269084ef8f62051da5fe458eb12`. This is a **source variant isolation**, not an override of product-dev, common review or G2 owner branch.

**One-writer isolation:** W8 / MI01 existing owner; protected PG / MI02 and independent A root/sink security owner; MI03/G9 source owner review unchanged. Existing 552 entries preserved except exact G2 authority variant. G2 `iam_session.py` and two G1/G2 owner tests added; no newly written runtime behavior. All additions are git-blob-exact original G2.

**Test target:** clean GitHub-hosted ephemeral pinned source test; manifest 555/555 checks; G2 50 original unit tests + ORG 4 packaging + 11 SQL regression in the *same process/source checkout*, distinct 65 existing tests; 0214 10 included inside G2 50. Build and W8 not tested in this review.

**Risk:** G2 D0 authority changes claim/publish behavior and may interfere with 0214/ORG. Capturing failures is valuable but not source promotion. D0 full restore rollback remains a deliberately reproduced replay vulnerability; real H01 grants/issuer/custody, PostgreSQL and production stay HOLD. Never accept a test red as a pass.

**Rollback:** close this review without merging, delete isolated candidate ref if needed after review, or normal revert of single isolated commit. Never force push shared refs or reset a consumed claim.
