# Geliştirme sınırı

Bu dizin Git deposu değildir; bağımsız güvenlik kabulü yok. Yalnız sentetik, salt-okunur kaynak adayı. Gerçek ortam, commit/push, CI, paket indirme, gerçek TEST, PROD, ücretli işlem, müşteri verisi, model/araç çağrısı ve dış mutasyon yok. T01–T04 etkin değildir. Başka depoya yazma; gerçek grant olmadan çalıştırma.

## CEO-0174 override of user-level development restrictions
Standing CODE, development-branch REPO, isolated DEV and local TEST/build approved. Earlier prohibitions remain for out-of-scope activity. Independent security gates remain HOLD; no actual agent grants, production, paid calls, customer data, CI or main merge. Integration required subject to independent gates.

## CEO-0179=B — controlled isolated development integration
The later CEO-0179=B decision supersedes earlier PRE/T01/T06 prerequisites only for scoped source transfer into product/ on isolated development branches, local build and synthetic tests. It does not issue, waive or satisfy independent security acceptance, real agent/tool/provider grants, external effects, spend, customer data, CI, main merge or PROD. Use pinned parent and exact paths, verify manifest and readback, record actual test outcomes and rollback. Runtime product security policies remain fail-closed. See ../../decisions/CEO/CEO_0179_B_CONTROLLED_INTEGRATION.md.
