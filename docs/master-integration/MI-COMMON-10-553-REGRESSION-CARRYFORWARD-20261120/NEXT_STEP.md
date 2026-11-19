# MI-COMMON-10 — Source-to-product next gate

1. Current source candidate: `a80932b6d5e99667889dfaa25b682feb267c6cba`, 553 files. `integration/product-dev` 505 files remains unchanged; owner review controls promotion.
2. Do not rerun unchanged 114 pinned-source tests or prior ORG 15 CI just to inflate counts; source provenance now established. W8 **full 553** dependency-reviewed prepare/install/test/smoke is first concrete end-to-end build blocker for MI-01 owner.
3. MI-07/08 independently address only the Windows native symlink-negative security case; prior 343 passing observations are not 344 single-run acceptance.
4. G2/G9 owner contract collision, trusted issuer/root custody, sink idempotent fencing, protected PostgreSQL and 8 IV negative cases remain separate gates; no production activation.
5. After exact test/log and owner approval, controlled source promotion via isolated branch/PR, not direct main or product-dev push. Keep 15/35/20/20/10 evidence rule and unchanged percentages until criterion completes.
