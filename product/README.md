# AI Company OS — Product v0.1.0-draft.3
D0 çevrimdışı kaynak adayı. Resmi CODE/REPO/DEV 0/3 etkin; NO_REAL_TEST / NO_PROD / NO_SPEND / NO_EXTERNAL_MUTATION. Önceki v140/draft.2 ayrı korunur. v135 ana hedef.

- W1: Phaser 6×6 layout, iki kat, dört oda, rezerv istasyon, kamera zoom, görsel BFS rota, avatar projection; gerçek ajan yok. Önceki SVG görünümü korunur.
- W2: backend-owned yeni fixture ve iki kapalı JSON schema, FE eş kopyaları. Beşinci GET: /demo/v1/core/preview; örnek plan ve replay read-model. FE yerel fixture, API bağlantısı yok.
- W3: pure DAG validation, deterministik dalgalar, QA/IV/release zinciri ve HOLD plan preview.
- W4: deny-only effect boundary, immutable sample Event Store ve DisabledT1 adapter sözleşmesi. Gerçek PEP/W-A/PostgreSQL yok.
- W5–W7: draft.2 katalogları korunur. W8: CORE_REVIEW.md 22 yeni inceleme oracle'ı; NOT_RUN.
- Offline HTML: önceki 13 görünüm + çekirdek inceleme paneli, örnek olay adımlama/gap. Phaser/Python çalıştırmaz.
- Dosyalar kaynak olarak yazıldı; ürün kodu, build, uygulama, tarayıcı, test, schema validation, kurulum, GitHub, dış işlemler yapılmadı. Bağımlılık pinleri aday; lockfile yok. Hash kontrolleri sadece dosya bütünlüğü.
- Yeni tasarım kararları (6×6 layout, örnek RESEARCH DAG, event adları, şemalar, ret kodları, API) teknik aday, normatif kabul değil. v139 kaynak-adayı istisnası açık; bağımsız kabul gerekli.

## 0181 — current isolated development state
Historical draft.3 notes above are preserved; CEO-0179=B authorizes isolated CODE/REPO/DEV/TEST. EDS and D0 diagnostic readback now integrated. Seven GET endpoints, guarded local proxy and panel, ephemeral SQLite sample replay. Backend selected product tests 24/24; TypeScript/Node 14/14, including real loopback GET. Exact pinned dependency environment, full frontend build/browser, independent acceptance, production and real operations remain unverified/HOLD. See ../docs/0181/ARCHITECTURE_AND_CATALOG.md.
