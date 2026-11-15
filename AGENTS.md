# AI Company OS — çalışma kuralları
Önce PROJECT_INDEX.md, handover/CURRENT.md ve handover/NEXT_STEP.md oku. Teknik gerçeklik sürümlü dosyalardır. Önceki kararları ve kaynakları koru; değişiklik, teşhis, rollback ve kanıt sınırlarını kaydet. 0158 aktarımı, 0159-A/B, 0160 ve 0161 kontrollü kaynak aday düzeni dar repo istisnasıdır; ürün AGENTS.md yürütme kısıtları korunur. Yeni yetkiler varsayma. Main merge, gerçek TEST, CI, PROD, harcama, sağlayıcı çağrısı ve bağımsız kabul yok. Her tur tam ZIP zorunlu.

14.11.2026 kullanıcı onayı: [sürekli kontrollü güncelleme aktarımı](decisions/CEO/CEO_REPO_TRANSFER_20261114.md). Mevcut yetki sınırlarında uygun geliştirme dalına aktarım için tekrar onay isteme; main merge ve diğer yürütme izinleri ayrıdır. Her tur aktarım sonucunu ve doğrulama durumunu devirde kaydet.

14.11.2026 [C çalışma yönü](decisions/CEO/CEO_WORK_MODE_20261114_C.md): kaynak ve yetki hazırlığı paralel; gerçek T01 ve bağımsız kabul koşulları değişmez. C kararını tekrar sorma.

14.11.2026 [0163 dar kaynak entegrasyonu](decisions/CEO/CEO_BOOTSTRAP_0163.md): kullanıcı açıkça dört sentetik frontend dosyasının R9 aday dalına entegrasyonunu istedi. Bu bir defalık kaynak istisnasıdır; sonraki ajanlara kalıcı source/repo grant vermez. T01/T06 gerçek bağımsız kabul ve T02/DEV/TEST/CI/PROD sınırları HOLD. Ürün AGENTS.md yürütme kuralları korunur.

14.11.2026 [0165 bounded R10 source integration](decisions/CEO/CEO_DIRECTION_0165.md): six exact original R10 files and two dashboard source changes only; new backend candidate quarantine. One-turn source exception, not runtime/standing expansion. All execution and independent acceptance gates remain HOLD.

14.11.2026 [0167 local MVP direction](decisions/CEO/CEO_DIRECTION_0167.md): nine pinned source promotions, manifest, preflight and documentation only; no actual package install/product runtime/test or independent grant. Read-only helper fixture verification is separate from product execution.

## CEO-0174 standing development
[Decision](decisions/CEO/CEO_0174_STANDING_DEVELOPMENT.md): CODE/REPO/isolated DEV/local TEST approved. Every round integrates where independent gates permit; record blockers, test evidence and rollback. Prior user-level prohibitions superseded only within this scope. No independent acceptance, CI, PROD, main merge, paid calls or real data.


## CEO-0179=B controlled continuous integration (2026-11-15)
[Decision](decisions/CEO/CEO_0179_B_CONTROLLED_INTEGRATION.md) and [policy](security/policy/CONTROLLED_DEV_INTEGRATION_0180.json) supersede independent PRE/T01/T06 prerequisites **only** for pinned isolated development-branch product source transfer, local build and synthetic tests. Keep actual independent security acceptance, real grants, external effects, spend, customer data, CI, main merge and PROD on their existing gates. No runtime policy change. Integrate actual product source where applicable, verify manifest, test only in allowed scope, record actual evidence, update catalog/tracker/handover and retain rollback. Prior historical instructions are not deleted. Do not ask for the same owner approval again.
