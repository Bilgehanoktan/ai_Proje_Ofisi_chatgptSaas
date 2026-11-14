# Scripts — rezerv
Bakım ve kaynak bütünlüğü yardımcıları; gerçek çalıştırma yetkisi ayrı. Bu tur executable dosya yok.

## 0167 read-only preflight
`verify_product.py` checks all product bytes and exact file set against an independently pinned manifest Git blob. `Prepare-Local.ps1` wraps it on Windows and prints tool versions. No package installs or product execution. The helper is not a security grant. Run before creating generated files in product/.
