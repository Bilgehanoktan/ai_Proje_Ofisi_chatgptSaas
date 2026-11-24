# Kaynaklar ve kanıt sınırı
Repo: https://github.com/Bilgehanoktan/ai_Proje_Ofisi_chatgptSaas/tree/recovery/0160-structure
R7 kaynak commit: c94a3e6ad4645188d51f9012311ace173cade100. Parent: 950794158cdb76f2d7031eaccfbe8dd4a1ba2733. İnceleme sırasında 0160 dalının son belgeleri de okundu; kaynak commit'teki ürün manifesti daha eski (0158) idi, dalın son hali 0160 manifesti içerir. Bunlar birbirine karıştırılmadı.

| GitHub yolu (dal) | Git blob SHA (alınan sonuçta mevcut) |
|---|---|
| handover/CURRENT.md | 47a5556009a58d4aee12eda39f58f073f1eb36a3 |
| handover/NEXT_STEP.md | 68481b0e9781bdff50a7705a5914127a2a38d57a |
| product/SOURCE_MANIFEST.json | 28d1b14d42bd2ce576ab955f7eb3e216191302ae |
| docs/architecture/DESIGN_MASTER.md | 0ca03306f05249a9567e6d37daa5bcac74479b25 |
| catalog/TECHNICAL_CATALOG.md | f2ad0387caf58bbe40940790ccccfc22c3fb52cf |
| docs/0158/R03_T1_PHYSICAL_MAPPING_0157.md | ea5698984409e85ecd31242c306143f92a740452 |
| docs/0158/R06_SCHEMA_CUSTODY_0149.json | 4edca7c88d8d8e1eb9ea59ab4cad84b49d6b36d6 |
| docs/0158/R07_R08_D14_D16_INCELEME_0158.md | 00ea264a0b3695de0c170094da721cc44ee877fb |
| docs/architecture/OWNERSHIP_MAP_0160.md | d35972385fff028885e2671f285a1cb78f58227a |
| contracts/PIN_REGISTRY_0159B.json | a72317c6cfbfe4a7d5199b3fff326d4e98e4e3a2 |
| product/ai-company-os-backend/app/engines/office_engine/layout.py | cf47623d303d21aed11eb5ee69b66a757c6a5d18 |
| product/ai-company-os-backend/app/core/transaction/fence_review.py | d922dab553ba96577a8247d4f4667ee967e2a5a5 |
| product/ai-company-os-backend/app/core/event_store/causal_review.py | bc4c8c92ab107bb96e255430cb1e174c4fa960db |
| product/ai-company-os-frontend/features/ceo-dashboard/Dashboard.tsx | 8228066163493768a77c99a7929533f4c50e3af6 |
| product/ai-company-os-frontend/office/engine/geometry.ts | 1e5934f4157bb52d43dd280649657af10a899da4 |

Ek olarak AGENTS.md (kök ve iki ürün), README, OPEN_ITEMS, OPEN_DECISIONS, TEST_EVIDENCE, CHANGE_RECORD, 0159B ARCHITECTURE_ADDENDUM, transaction/review ve port, lifecycle, iv_review, outbox_review, gateway, API ve DB katalogları, office/core fixture ve schema okundu. Bu SHA'lar connector'dan dönen Git blob kimlikleridir, SHA-256 değildir. Tüm R7 dosyaları yerel olarak indirilmedi. 0160 tam ZIP yok; sadece bu inceleme deltası için yeni SHA-256 manifesti oluşturuldu. Önceki kaynak manifestinin 114/114 ve test sayıları önceki rapordan aktarılmıştır.
