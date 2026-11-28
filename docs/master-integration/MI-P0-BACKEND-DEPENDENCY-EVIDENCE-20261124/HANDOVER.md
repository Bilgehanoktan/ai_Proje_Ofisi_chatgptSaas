# MI-P0 — 24.11.2026 Windows checkout ve C50 bağımlılık kanıt devri

**Durum: REVIEW_ONLY / HOLD.** H01 bu kayıtların GitHub'a aktarılmasını istedi. Bu kayıt ürün kabulü, bağımsız güvenlik onayı veya yeni CI/PROD yetkisi değildir. Kanonik kaynak ve merkezi kuyruk değiştirilmez; merkezi sahip incelemesi için ayrı taslak dal.

## Kanıt ve sonuç
- Windows PowerShell 5.1 kullanıcı koşumu: GitHub kimlik doğrulaması, PR #19/#46/#47 tam commit checkout, temiz worktree 3/3 PASS, altı kritik blob 6/6 PASS. Kimlik bilgileri ve kişisel dosya yolları aktarılmadı.
- R1/R2 Python yol/PowerShell tırnak hataları; R3 Python 3.13.17 ve 25 binary wheel download PASS, kurulum yok. Eski 46.0.4 kilidi onaysız.
- R4: cryptography 50.0.2 adayına geçiş; 24 hash aynı, yalnız 1 wheel değişti. R4 raporu PyPI 25/25 hash eşleşmesi bildiriyor; attestation imzası NOT_RUN. Gerçek arşiv ve wheel baytları bu aktarımda salt okunur yeniden denetlendi: CRC, 25/25 SHA-256, 25/25 lock/inventory, 809/809 RECORD hash/length, Windows CPython 3.13.17 için 34/34 aktif Requires-Dist bağlantısı ve 25/25 Requires-Python PASS. Bunlar kurulum veya ürün testi değildir.
- Aday kilit: [python.lock.C50.CANDIDATE.txt](python.lock.C50.CANDIDATE.txt), SHA-256 942ec4a790e746e18dfaa5a9d666bef17d27dc0efa4f764259afc0ee4e266eec. **DO NOT INSTALL**. Kaynak requirements-history-signatures.txt hâlâ 46.0.4; pin geçişi onaylanmış sayılmaz. W8 28-wheel graph farklıdır, bu 25-wheel graph ile eşitlenmez.
- [EVIDENCE.json](EVIDENCE.json): arşiv ve iç dosya SHA-256, kaynak HEAD'leri, test hedefleri, önceki/güncel değerler, sorumlular. Orijinal ZIP ve wheel binary'leri kullanıcı kanıtı olarak dışarıda korunur; lisans ve boyut nedeniyle repo içine kopyalanmaz.

## Güvenlik / lisans
C50 Windows wheel içindeki cryptography/hazmat/bindings/_rust.pyd baytlarında OpenSSL 4.0.3 29 Sep 2026 string'i görüldü. Bu, runtime sürüm sorgusu değildir. OpenSSL'in 10.11.2026 tarihli [resmî bildirimi](https://www.openssl-library.org/news/vulnerabilities-4.0/index.html) CVE-2026-95692 için Low önem derecesi ve 4.0.4 öncesi 4.0.x etkilenme aralığı verir. Ürün erişilebilirliği/istismar edilebilirliği kanıtlanmadı; MI-01 ve bağımsız Security/IV incelemeli. PyPI paket düzeyi boş vulnerability listesi native kütüphane güvenliğini kanıtlamaz. Lisans metadata varlığı yasal onay değildir; dağıtım, üçüncü taraf notices ve provenance HOLD. Yeni kurulum ve güvenlik kabulü yok.

## Açık işler ve sahiplik
| İş | Durum | Sahip / sonraki |
|---|---|---|
| PR #50/#51 MIME 34+65 özgün test | Önceki bildirilen 99/99; yeni koşum yok | MI-05/06 kaynak sahipleri; onay ve merkezi manifest |
| PR #19/#46/#47 checkout | 3/3 PASS | MI-03/04 ve 03API; immutable kaynakları koru |
| G7 7 ve API 9 özgün test | 0/16 NOT_RUN | Mevcut import zincirinin tamamını incele, kripto gerektirmeyen onaylı bağımlılık altkümesi mümkünse ayrı çalıştır |
| IAM 12 özgün test | 0/12 NOT_RUN | MI-03/04; cryptography ve imza zinciri, NW02 authority seçimi |
| Merkezi manifest / entegrasyon | HOLD | Tek yetkili merkezi yazar, PR47 iki manifest farkı ve NW02 owner kararı |
| W8 | 3/8 -> 3/8, delta 0 pp | MI-01; bağımsız ön inceleme, tam resmî C07, gerçek Chromium C08, bağımsız C05, kabul |

Tasarım/kod/katalog/manifest/API/DB/event değişikliği 0. Ağırlıklı geliştirme HESAPLANAMADI; 24 alan ordinal değerleri yeniden hesaplanmadı. Yeni CEO kararı gerekmez; owner ve bağımsız güvenlik yetkisi ayrı. Bu devir kaydı merkezi kuyruk güncellemesinin yerini tutmaz. Rollback: yalnız bu üç yeni kayıt için normal revert veya taslak PR'ı kapatma; hiçbir eski kaynak/kanıt/dal silinmez.
