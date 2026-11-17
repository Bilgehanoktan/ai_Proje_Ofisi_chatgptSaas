# Archive inventory and reconstruction
Original ZIP containers retained locally; GitHub stores their source/evidence files and exact manifests, not the original binary ZIP bytes.
- ORG-02R2_candidate.zip SHA-256 6055776eeac22035213eacb7c5dd6e586e547e707df86b819d22605f920785ef
- ORG-02R3_candidate.zip SHA-256 d9b72dcc95bcb09080c6da524f6355a684f2c3f559b9d5e189fba5e3d48a7220
- ORG-03_candidate.zip SHA-256 b36f1ffb6756fdf976ecfd62291bf691f98ca993a61d928bd9a952cde85ac537
Each manifest's Python files reside unchanged at candidates/ORG-04; HANDOVER.md, test.log and SHA256SUMS live in the matching history directory. ORG-03 PARENT_HANDOVER.md, PARENT_TEST.log and PARENT_SHA256SUMS are respectively ORG-02R3 HANDOVER.md, test.log and SHA256SUMS. Copy to a separate directory with original names to verify its SHA256SUMS. This reconstructs files, not the original compressed archive bytes. ORG-02 original source/test are in the current directory, original test.log under history/ORG-02. No canonical promotion.
