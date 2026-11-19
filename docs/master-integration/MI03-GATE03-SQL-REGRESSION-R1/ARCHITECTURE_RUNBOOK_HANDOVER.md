# MI03-GATE03-SQL-R1 central technical catalog and handover

## Proven source and tests
Source candidate: d6b82dc412b7bb0f048ece2fd43fe83f6627cc59, previous candidate 65a0e978c20378041e98f70e6ed074151214a3bb, parent common 61bb06efbba7544bfc68260ed8eb4d342cab9b8e. Added one new product test `product/ai-company-os-backend/tests/test_org_sql_runtime_mi03.py`. Exact owner SQL `schema.sql`, `operations.sql`, and `assignment_review.sql` were verified 3/3 by Git SHA-1 blob and SHA-256. New 11/11 PASS on real temporary SQLite (Python 3.13.5, SQLite 3.46.1; 0.227s, exit0); source log and executable source stored in candidate repo. Manifest 552 entries/553 product files with full remote readback. Tests cover schema constraints/immutable triggers, duplicate run/digest, D0 state revisions, org notices HOLD, foreign key. Evidence: [original candidate log](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/blob/d6b82dc412b7bb0f048ece2fd43fe83f6627cc59/docs/master-integration/MI03-GATE03-ORG-RUNTIME-CLOSURE-01/org-sql-11.log).

## Parallel work reconciliation
Another owner concurrently executed 71/71 selected tests on the former 65a0 candidate, including four original packaging smoke tests; 59 existing tests rerun and eight new supplemental. Do not add the two totals as one full product suite. That work identified missing actual Core `research_slice` in selected-stage test closure; positive OperationsStore assignment/actual issuer is NOT_RUN. This SQL-only result neither substitutes that Core readback nor changes G9 7, G2 50, Memory-T1 10 or W8 build obligations. Full product and independent acceptance HOLD, same role/authority boundaries and no signed trust root. Joint owner review of org namespace and durable_ops 41-line extension required.

## Runtime and rollback
No API, live DB, grant, customer data, provider, CI, main or PROD touched. Run test only on a clean pinned checkout from backend root: `python -B -m unittest discover -s tests -p test_org_sql_runtime_mi03.py -v`. Test auto-creates disposable SQLite. Never apply owner SQL as a production migration. On pin/test mismatch HOLD; compare exact owner originals, do not repin old G9 runner. Revert isolated candidate normally to 65a0 if necessary; retain logs, previous source hashes and review history.

## Next owner tasks
1. Run Core source-complete `research_slice` and `OperationsStore.record_assignment_review` positive/negative synthetic replay with exact source pins (owner provenance still HOLD).
2. G9 original 7 and G2 original 50 separate; actual 0214 10 Memory-T1, W8 full build and PostgreSQL strict COMMIT.
3. Owner review/approval without enabling actual grants; independent acceptance separate.
