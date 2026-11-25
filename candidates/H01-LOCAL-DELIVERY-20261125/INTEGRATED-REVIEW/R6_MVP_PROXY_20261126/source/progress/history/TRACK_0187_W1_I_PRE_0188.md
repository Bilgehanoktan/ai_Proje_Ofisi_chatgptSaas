# TRACK-0187-W1-I

Olgunluk puanları, tamamlanma yüzdesi değildir. Kanonik kaynak: [DEVELOPMENT_TRACKER_24.json](DEVELOPMENT_TRACKER_24.json).

| ID | Alan | Tasarım | Kaynak | Kanıt |
|---:|---|---:|---:|---|
| 1 | Frontend | 75 | 50 | 24 Node tests; actual compiled proxy 200/503, source UI mounted; React NOT_RUN  /  0187-W1-I: combined UI/0187 source; 66 selected Node/mock checks, 2 syntax; 9 schema + 4 fixture pairs; full product NOT_RUN |
| 2 | UI/UX Design System | 50 | 50 | Prior 14-file EDS integration unchanged; current EDS smoke source added  /  0187-W1-I: combined UI/0187 source; 66 selected Node/mock checks, 2 syntax; 9 schema + 4 fixture pairs; full product NOT_RUN |
| 3 | Office Engine | 75 | 50 | Exact role-template station mapping from real CLI sample DB; no live movement or geometry join  /  0187-W1-I: combined UI/0187 source; 66 selected Node/mock checks, 2 syntax; 9 schema + 4 fixture pairs; full product NOT_RUN |
| 4 | API & Contracts | 75 | 50 | Byte-identical schema, 20 common vectors, real isolated 200/503  /  0187-W1-I: combined UI/0187 source; 66 selected Node/mock checks, 2 syntax; 9 schema + 4 fixture pairs; full product NOT_RUN |
| 5 | Backend | 75 | 50 | 17 Python selected including actual writer; full backend not run |
| 6 | Orchestrator | 75 | 50 | Existing canonical plan compiler used by actual Workbench writer; new projection consumes persisted history |
| 7 | Task Engine & DAG | 75 | 50 | Actual five sample tasks and six readback prefixes; IV/release HOLD  /  0187-W1-I: combined UI/0187 source; 66 selected Node/mock checks, 2 syntax; 9 schema + 4 fixture pairs; full product NOT_RUN |
| 8 | Agent Runtime | 75 | 25 | Actual writer lease plus strict historical readback; no trusted clock |
| 9 | AI Model Gateway | 50 | 25 | Existing fixed adapter exercised by actual writer; no provider invocation |
| 10 | Skill & Tool Engine | 75 | 25 | Prior skill/capability checks rerun; no effective tools |
| 11 | Database | 75 | 25 | Existing SQLite read transaction; no migration or PostgreSQL |
| 12 | Event Store & Messaging | 75 | 50 | Exact event sequence, command and digest verification; no SSE |
| 13 | Memory & Knowledge | 75 | 25 | Existing source retained |
| 14 | Security & IAM | 75 | 25 | Composite membership FK and exact scope checks; not real IAM  /  0187-W1-I: combined UI/0187 source; 66 selected Node/mock checks, 2 syntax; 9 schema + 4 fixture pairs; full product NOT_RUN |
| 15 | Independent Verifier | 75 | 25 | Witness reference shape review only; no independent verifier acceptance  /  0187-W1-I: combined UI/0187 source; 66 selected Node/mock checks, 2 syntax; 9 schema + 4 fixture pairs; full product NOT_RUN |
| 16 | SaaS & Multi-Tenant | 75 | 25 | Fixed synthetic membership and ownership link, wrong scope tests  /  0187-W1-I: combined UI/0187 source; 66 selected Node/mock checks, 2 syntax; 9 schema + 4 fixture pairs; full product NOT_RUN |
| 17 | Ürün ve iş modülleri | 75 | 25 | Prior source retained  /  0187-W1-I: combined UI/0187 source; 66 selected Node/mock checks, 2 syntax; 9 schema + 4 fixture pairs; full product NOT_RUN |
| 18 | Dış sistem entegrasyonları | 75 | 0 | No external integration |
| 19 | Finans & Billing | 75 | 25 | Durable fixed reservation, known sample settlement and UNKNOWN hold  /  0187-W1-I: combined UI/0187 source; 66 selected Node/mock checks, 2 syntax; 9 schema + 4 fixture pairs; full product NOT_RUN |
| 20 | Test & QA | 75 | 25 | 41 new tests and real CLI/loopback; 111 prior NOT rerun  /  0187-W1-I: combined UI/0187 source; 66 selected Node/mock checks, 2 syntax; 9 schema + 4 fixture pairs; full product NOT_RUN |
| 21 | DevOps & Infrastructure | 75 | 25 | npm EAI_AGAIN; pinned Next build/PG unavailable  /  0187-W1-I: combined UI/0187 source; 66 selected Node/mock checks, 2 syntax; 9 schema + 4 fixture pairs; full product NOT_RUN |
| 22 | Monitoring & Observability | 50 | 25 | Historical role counts, no real freshness or telemetry |
| 23 | Backup & Disaster Recovery | 75 | 25 | Reopen is not backup or disaster recovery |
| 24 | Teknik katalog & dokümantasyon | 75 | 75 | 212/212 path/size; 16 changed +27 support exact  /  0187-W1-I: combined UI/0187 source; 66 selected Node/mock checks, 2 syntax; 9 schema + 4 fixture pairs; full product NOT_RUN |

Ordinal maturity scores unchanged from 0187. 32 W1 UI paths integrated (30 exact, two reconciled), 66 selected Node/mock tests PASS, 2 merged TSX syntax PASS; 9 contract and 4 fixture pairs match. Full product, backend, Next, React/browser and visual regression NOT_RUN. Independent acceptance HOLD.
