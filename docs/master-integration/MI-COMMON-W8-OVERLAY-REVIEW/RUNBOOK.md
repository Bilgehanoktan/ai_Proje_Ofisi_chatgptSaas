# MI-COMMON-W8-OVERLAY-REVIEW-01

Independent supplemental local mechanics review of common candidate `bf87d5c48c7fee97fe12d0a28df3be80249f7306`. The already-published common source review is reused; no second product candidate, product source or owner branch mutation. This is not owner approval, a production safety guarantee, full W8 audit or a real DB test.

## Reproduction and maintenance
Use a fresh isolated directory. Copy the five exact candidate files to the local names in EVIDENCE.json, verifying Git blob and SHA256 before execution. Copy the supplemental test here unchanged. Run Python 3.13.5 `python -I -B test_unified_u3_runner.py -v` then `python -B test_common_history_overlay.py -v` from that directory. No product install, credentials, provider or database access is required. Historical and current transports are read as bytes, not imported. The original 10 tests mock parent/build/browser. The four supplemental tests use an actual one-entry materialization and a mocked parent for load/bind order; the full historical lock is not executed. Missing or changed history must remain a HOLD; never fall back to current product source or re-pin the old lock. Run full historical regression, original W5/Memory regression and W8 audit/prepare/fresh fingerprint on a connected exact checkout separately.

## Catalog / architecture delta
- Existing W8 `load_candidate` and P24 `materialize_locked`: verified isolated history binding and copy, no implementation changes.
- New evidence-only `test_common_history_overlay.py`, class CommonHistoryTests, four methods; Python stdlib unittest, pathlib, tempfile, types, unittest.mock, hashlib; no API/database/dependency/permission changes.
- Preserve T1 current transport and original historical source independently. G6A protected entry, G8 actual assignment/role provenance, strict durable commit, independent custody remain unratified/NOT_RUN.
- Rollback: remove this supplemental evidence pointer from the central queue by reviewed revert; do not change source branches, force-push, restore databases or remove original owner evidence.

## Handover
10/10 original runner mechanics + 4/4 new supplemental mechanics passed; 5/5 local exact source pins. These are not 14 product integration tests. No development percentage or product acceptance increase. Product-dev and common candidate unchanged. Continue central owner review and non-conflicting MI05/06/09 only as already queued; protected COMMIT stays HOLD.
