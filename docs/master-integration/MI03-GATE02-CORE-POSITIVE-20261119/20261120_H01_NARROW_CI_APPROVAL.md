# H01 — GATE-02 PR #6 dar kapsamlı sentetik CI izni (2026-11-20)

Kullanıcının "ben onay veriyorum ilerlet" kararı, kendisine sunulan **PR #6 üzerinde ayrı, dar kapsamlı salt-okunur sentetik GitHub Actions koşumu** teklifine açık onaydır. Önceden verilen MI-10 PR #4 iznini başka bir işe taşımak değildir.

## Pozitif kapsam (yalnız bir sınır)
- Depo: `Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas`; yalnız **taslak PR #6** (`review/mi03-gate02-core-positive-20261119` → `integration/mi03-gate03-org-runtime-closure-01`); aynı depo PR koşulu.
- Tek yeni workflow: `.github/workflows/mi03-gate02-limited-ci.yml`.
- Yetki: `permissions: contents: read`, `actions/checkout` için `persist-credentials: false`, sabit Git SHA'lı Action sürümleri, izole GitHub-hosted geçici runner.
- Koşum: PR #6'nın HEAD commit'i tam checkout; 553 girdilik özgün `product/SOURCE_MANIFEST.json` üzerinden SHA-256 + boyut bütünlüğü, 12 özgün sahibi Git blob pinleri, yalnız `test_core_operations_assignment_mi03.py` içindeki 10 sentetik D0 SQLite unittest senaryosu.
- Bağımlılık gerekiyorsa yalnız sürümlü ve test için gerekli sentetik Python wheel'ler; gerçek veritabanı, secret, canlı ajan, harcama veya dış etki yok.
- Ham log, test adı, başarılı/başarısız/atlanan, exit code, PR SHA ve veri yokken yalnız sentetik hata çıktısı; testin tamamını PASS saymak için tam 10/10 gerçekten çalışmalı.

## Yasak ve HOLD alanları
Gerçek IAM issuer/rol, grant/credential, gerçek müşteri verisi, canlı provider/tool, secret/OIDC, PROD, deploy, bütçe/hazırlanan harcama, main/product-dev yazımı, PR otomatik merge, bağımsız güvenlik kabulü, PostgreSQL COMMIT, G9/G2/Memory-T1 ve W8 native browser **izne dahil değildir**. Var olan PR #4 workflow ve kapsamı değişmez. PR #6'nın asıl üretim/test modüllerinde düzeltme olursa sahibin ayrı kaynak incelemesi gereklidir.

## Geri dönüş / kanıt
PR #6 kapatma ya da yalnız bu workflow ve sınırlı kanıt kayıtlarının normal revert edilmesi; force push, önceki test kaydı/hak silme yok. CI başarısı yalnız sentetik D0 fonksiyonel doğrulamayı kanıtlar; proje kabulü otomatik yükselmez.

Kaynak sabit taban: `integration/mi03-gate03-org-runtime-closure-01@d6b82dc412b7bb0f048ece2fd43fe83f6627cc59`; ürün ana tabanı `integration/product-dev@8a3b05aadd32b214f3f8988fc9c793f853fbe3d0`.
