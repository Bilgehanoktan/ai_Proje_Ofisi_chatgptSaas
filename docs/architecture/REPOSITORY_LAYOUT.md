# Klasör standardı — 0159-A aday
Mevcut product/ai-company-os-frontend ve product/ai-company-os-backend konumları korunur. docs/0158 ve IMPORT_MANIFEST_0158.json tarihsel snapshot olarak değişmez.

| Alan | Hedef | Durum |
|---|---|---|
| UI ve ofis | product/ai-company-os-frontend/app, features, office | mevcut |
| Core | product/ai-company-os-backend/app/core | mevcut |
| AI, skill, memory | backend app/engines | aday, 0159-B |
| Contracts | contracts/ | indeks; backend source, frontend generated |
| Database | database/ | rezerv; fiziksel eşleme HOLD |
| Workers | workers/ | rezerv |
| IV | verifier/ | rezerv; bağımsız güven gerekli |
| Integrations | integrations/ | rezerv; PEP zorunlu |
| System tests | tests/ | rezerv; ürün testleri yerinde |
| Infrastructure | infrastructure/ | rezerv; CI/kurulum yok |
| Governance | docs/, catalog/, decisions/, handover/, progress/ | indeks |
| Security, releases | security/, releases/ | indeks |
| Config, scripts, examples | config/, scripts/, examples/ | rezerv |

Geçiş: parent ve hashleri sabitle; import/sahiplik/bağımlılık envanteri çıkar; taşıma adayını ayrı commit yap; eski-yeni yol eşlemesi ve rollback kaydet; manifest ve sözleşme pinlerini güncelle; yalnız izinli doğrulamalar yap. Boş runtime paketi veya etkin workflow oluşturma. Klasörler yeni normatif karar değildir.
