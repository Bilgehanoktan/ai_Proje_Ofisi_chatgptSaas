# AI Company OS — MI-P0 | 4/4 ORG paketleme kapısı ve kaynak çakışması ayrıştırma

**20 Kasım 2026 — Master Integration / kanıta dayalı gerçek D0 CI kapanışı**

## Ne, neden, nasıl, nerede
Mevcut PR #9'un tam paketleme testinde `0/4 NOT_RUN` görünen somut engel, diğer sahip hattının izinli **PR #11** GitHub CI çalışmasıyla **4/4 PASS** olarak kapandı. Bu tur yeni workflow, test dosyası veya ürün kaynağı oluşturmadı; `planning/master-integration-governance` üzerindeki kanıt, teknik katalog, ilerleme ve devir kayıtlarını güncelledi. Ayrıca çakışan PR #7'nin kanıtları exact Git blob içerikleri korunarak merkezi kayıt altında saklandı; eski çakışan ilerleme JSON'ları kullanılmadı.

## Değişmez kaynak ve gerçek test
- Kaynak: `integration/mi03-gate03-org-runtime-closure-01@d6b82dc412b7bb0f048ece2fd43fe83f6627cc59` / 553 ürün dosyası / 552 manifest girdisi.
- Çalıştıran taslak inceleme: [PR #11](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/pull/11); CI kaynak head `69c530157f6e50db7515fadfe630d80c454983f6`, yalnız workflow `.github/workflows/mi03-pr9-owner-package.yml`, blob `51fc2a6daa2e4c4105b1f3741d00de6a4b9e5f9d`.
- Run: [#44628704044](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44628704044), job `135929295468`, `ubuntu-24.04`, Python `3.13.5`, SQLite `3.45.1`. Ham logda **552/552 SHA-256+byte PASS**, `Ran 4 tests in 1.469s; OK`, `Ran 11 tests in 0.203s; OK`. Tüm ilgili job adımları SUCCESS.
- **Fark:** Önce 4 özgün paketleme testi `NOT_RUN`; şimdi **4/4 gerçek GitHub CI PASS**. Önceki 11 SQL yöntemi zaten tarihsel PASS idi; şimdi **11/11 yeniden PASS**, benzersiz yeni yöntem sayılmaz.
- **Sınır:** Sentetik SQLite D0. Gerçek issuer/role, root/claim, PostgreSQL strict protected COMMIT, external effect sink, eski restore/replay açığı, W8 full native, bağımsız IV ve MVP kabulüne kanıt değildir.

## Teknik katalog / çakışma kararı için güvenli inceleme
| Dosya/eksen | Önceki owner blob | Aday blob | Somut kaynak farkı | Dispozisyon |
|---|---|---|---|---|
| `durable_ops.py` (ORG/G9) | `43ed448c02904ab44b3cf8665f4aeafb0a38f10a` | `619fe224c05d7f7f7efe998583e4730cb2cb4d3e` | Eski 162 fiziksel satır sırayla korunmuş; +41 satır, 0 silme. `initialize_assignment_ops()`, `OperationsStore.record_assignment_review()`, `OperationsStore.assignment_review()` eklenmiş | **STATIC ADDITIVE COMPATIBILITY; OWNER_RATIFICATION_HOLD** |
| `intent_authority.py` (G2/Authority) | `fa47acd32adb309896f762ec50e47bf26641adbb` | `b28788f46a39c282d79d29c4abd817ed5fc9de99` | Eski 148 vs yeni 173 satır; `create(..., *, iam_bootstrap=False)` ve `claim_and_fence(..., *, session_check=None)` isteğe bağlı parametreleri, `_iam_mode`/`_check_iam` kontrolü, IAM HOLD davranışı. Doğrulanmış bağımsız root değil | **TWO_OWNER_VARIANTS; KEEP CANONICAL AND G2 PINNED; OWNER_RATIFICATION_HOLD** |
| `assignment_lifecycle.py` ve `assignment_review.sql` | 539 ortak kaynakta yok | PR9'da 14 yeni dosyanın bir kısmı | 4 paketleme ve 11 SQL özgün testi geçti; gerçek PostgreSQL ve IAM köken doğrulaması yok | **PACKAGE_SMOKE_GATE_CLOSED; SECURITY_HOLD** |

**Önemli:** GitHub'ın PR #9 için `mergeable=true` göstermesi veya eski 538/538 manifest girdisinin korunması *owner onayı* değildir. Aynı zamanda `compare status=diverged (ahead 2, behind 5)` kaydı, otomatik olarak bir dosya birleştirme çatışması kanıtı da değildir; yalnız fast-forward yapılamayacağını anlatır. 14 yeni dosyayı mevcut `integration/product-dev` dalına izinsiz ve tam W8/PG olmadan taşımayız. `G2/Authority` yerleşimi ayrı tutulur, kaynak yeniden yazılmaz.

**Yeni API / DB / class / function / dependency:** Bu tur hiçbir yeni ürün sembolü, endpoint, SQL migration, dependency veya workflow oluşturulmadı. Buradaki isimler **mevcut PR9 owner kaynaklarının katalog referansıdır**. Bağımsız güvenlik tasarımı Option A seçilmiş olsa da sağlayıcı ve sink kullanılabilir değildir.

## Risk, arıza teşhisi, bakım ve rollback
1. **Manifest uyuşmazlığı:** 552/552 dosya baytı/SHA-256 CI PASS; değişim veya kopuk checkout olduğunda mevcut PR11 job logu ve kaynak SHA kıyaslanır, farklıysa yeniden owner incelemesi yapılır.
2. **Yanlış PASS yükseltmesi:** 4/4 özgün paketleme testleri sadece D0 import/colocation/immutable SQLite ve HOLD korumasını kanıtlar. G2/G9 özgün testleri, protected PG, W8 ve IV için ayrı kabul gerektirir.
3. **İki yazıcılı JSON çatışması:** PR #7 kaynak dokümanları exact Git blob eşleşmesiyle mevcut governance'a alındı; eski PR diff'teki `MASTER_INTEGRATION_CURRENT.json` / `PARTIAL_PROGRESS.json` otomatik merge edilmeyecek. Güncel JSON indeksi additif korunur.
4. **Geri dönüş:** Governance doküman + ilgili progress kayıtları normal revert. `integration/product-dev@8a3b05aadd32b214f3f8988fc9c793f853fbe3d0` ve `main` değişmedi. Owner PR9/11 kaynakları ve önceki commitler korunur; force push yok.

## Geliştirme ve kabul
Ağırlıklar: tasarım %15 / kod %35 / fonksiyonel %20 / entegrasyon %20 / nihai kabul %10. Genel kriter paydası onaylı değil: önceki ve güncel **HESAPLANAMADI**, delta yüzdesi uydurulmadı. MI-03 kayıtlı gelişim **%42,5→%42,5**. Core ürün kabulü **12/16→12/16**, UI **21/40→21/40**, MVP **0/11→0/11**, değişim **0 yüzde puan**. Bu tur **4 yeni PASS *kanıtı*** vardır, dört yeni test yazılmamıştır.

## Sıradaki gerçek kapılar
1. PR9 ORG/G9 41-additive-diff owner seçimi; IAM/G2 authority varyantı owner seçimi (kanonik D0 local otorite halen güvenlik hold).
2. Özgün G2 50, G9 7, Memory–T1 10 regresyonları, tam W8 original lock+browser ve strict PG/restore.
3. Bağımsız Option A root/issuer/custody/sink/fencing ve IV onayı olmadan gerçek COMMIT veya production kabulü **yok**.

**Makine kanıtı:** [EVIDENCE.json](EVIDENCE.json).
