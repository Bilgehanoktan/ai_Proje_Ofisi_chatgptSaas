# MI03/A — Source-only ORG/Core controlled integration candidate (2026-11-20)
## Kaynak ve neden
Kullanıcının entegrasyon izni ve D03/D04 A güvenlik yönü dikkate alınarak mevcut 539 dosyalık common adayın ürün ağacına **yalnız özgün 14 dosyalık ORG/Core uzantısı** aktarılır. Önceki 538 manifest kaydı birebir korunur. Ortak `docs/architecture/DESIGN_MASTER.md`, `handover/CURRENT.md` ve `handover/NEXT_STEP.md` üzerine owner adayının tarihsel dokümanları yazılmaz. Bu fark, daha geniş kapsamlı PR #9 yerine dar tek-yazıcı aktarım için hazırlanmıştır.

- Baz: `integration/mi-common-source-review-01@59c0fc505ca286e681ed0965ee317eadf571a806` / product tree `617e1ca5f5b657d9fe8ad09017a60ecd47ce6bad`.
- Özgün owner ürün ağacı: `integration/mi03-gate03-org-runtime-closure-01@d6b82dc412b7bb0f048ece2fd43fe83f6627cc59` / product tree `f4cdcf68115917ab69ba6441414539fe32a59369`.
- Yeni aday yalnız bu owner ürün ağacına byte-exact eş olacaktır. `product-dev` ve `main` değiştirilmez.

## Gerçek test
[PR #11 izole test koşumu](https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/actions/runs/44628704044) GitHub runner üzerinde **SUCCESS**. Python 3.13.5, SQLite 3.45.1; tam 552/552 manifest SHA-256+bayt, özgün 4/4 paketleme ve 11/11 SQL test PASS. Bu 15 test aynı kaynak ürün ağacına aittir. PR #6 Core–OperationsStore 10/10 tarihsel, ikinci kez sayılmaz. G2/G9/Memory T1, real PG ve W8 tamamlanmadı.

## Kaynak-sahipliği ve güvenlik
G9 `durable_ops.py` 162 satırı korunur, 41 satırlık D0 uzantı mevcut. Bu değişim yeni gerçek issuer değildir. G2 `intent_authority.py` farklı versiyon sorunu sürer ve bu aktarımda düzeltilmez. Bağımsız consensus root, consume claim, sink-side fence/idempotency ve gerçek IAM/ORG yetki kökeni mevcut değildir. D0 eski DB+pin restore açığı açık; sistem HOLD/deny, otomatik retry yok. A bağımsız sekiz negatif test **0/8**, gerçek üretim güvenlik kabulü **yok**.

## Mimari/test bakım ve sonraki işler
Birleştirme, yalnız owner/yetki korumaları ve bağımsız testlerden ayrı **kaynak aşamasına** işaret eder. `product-dev` aktarımı ancak Unified U3B tam build, reviewer pin, G2/G9 bağımlılık ve ayrı güvenlik kapılarıyla ele alınır. SQL'leri mevcut veritabanında çalıştırma; yalnız izole disposable test DB. Arıza: manifest/hash farkında HOLD; owner API sözleşmesi farkında HOLD; fail closed. Geri dönüş: kaynak-only commit normal revert; root/consumed claim geçmişini asla silme.

## Katalog ve ilerleme
Bu tur kaynak inceleme kanıtı yeni çalışma alanında yaratılmıştır; IAM/ORG tarihsel **%42,5→%42,5**, global geliştirme HESAPLANAMADI, kanonik Core **12/16**, MVP **0/11**, IV **0/7**, A bağımsız negatif **0/8**, ürün kabul farkı 0. Önceki test kayıtları korunur. Tam katalog: `TECHNICAL_DELTA.json`.
