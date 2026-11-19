# MI-04-G5-WINDOWS-EVIDENCE-READBACK

Historical Windows G5/G4 26/26 on 1a9464966c1c5c67415e279b20bae3b19107554c; 31 source pins. Existing evidence afba55652d4667d9027a0a7fd8f2dec47684480 is a console reconstruction, not independent execution. One distinct run, no repeat counting. GitHub tree comparison: G7 31 exact, G6A 30 exact/1 divergent (intent_authority.py), common 11 exact/1 divergent/19 absent; of 17 product pins, 11 exact/1 divergent/5 absent. See CATALOG_AND_EVIDENCE.json for every path.

## Architecture / maintenance
No new engine, API, schema, dependency, grant, writer, or product changes. Preserve existing explicit protected entry recommendation and GATE-01 owner HOLD; G5 readback is not live assignment provenance, shared publication, PostgreSQL or strict COMMIT. Original G7 closure can reuse historical evidence; G6A substitution requires owner review and separate replay, not a claimed PASS. No Windows command now. Existing MI-05/06 and MI-07/08 work preserved.

## Next / rollback
Owners T1/IAM/D4 and ORG retain source control. GATE-01 and GATE-02 in parallel; GATE-03/04 then GATE-05. Recover MEM05E-R1 raw logs; retain original G2 50/G9 7/G6A/R8 and 344 runner scopes. No score or gate change. If later found incorrect, revert this governance-only delta; never restore old writer into IAM-backed store. Product-dev/main and all source branches unchanged by this commit.
