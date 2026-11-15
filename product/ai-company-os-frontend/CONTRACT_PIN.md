# D0 contract pin — draft.3
Backend source owner candidate; frontend byte-identical consumer. Not normative KS/NS acceptance. No runtime validation.
- `company.catalog.demo.schema.json` SHA-256 `11b688e725933075ced435aba0d283c8a2b2df78896f7c5129a2cc673e9523a3`
- `core.preview.demo.schema.json` SHA-256 `7bda9468606128af2acbd0616556c47ce91b69806af1e739122919ec3ba6d74c`
- `core.preview.response.schema.json` SHA-256 `22385a4a86b51ce0b858a0d194be2bf46d02ff6b3221f63192cc82e7a2f5ee53`
- `office.snapshot.demo.schema.json` SHA-256 `f7191fa16fdfad020dcdf7cec0506f874b398c6afba6d25a734a0440c6e5ce9d`
- `company.catalog.json` SHA-256 `f27745df5af32a68d1bf3aed6ec4c014d5047fa6ac70bb3e498ce86a2f0c5059`
- `core.preview.json` SHA-256 `3f06282142ca685f21cce6a83ebb6341fe3b8c470027b912662c6d879f15256b`
- `office.snapshot.json` SHA-256 `313b8072ec1e4bdc1feb945540c31e0a762be4151f616bd6a25e4772a790baa5`

## 0155 R09 D0 additive candidate (v0 retained)
- `core.plan.projection.schema.json` SHA-256 `4e1b26ae8a122807351d7d6cbe6ba0e051de9171a93a0248070b22869c828421`
- `core.plan.projection.json` SHA-256 `e564bed4f4edfb5dd94488b08cbba3205b6f018491fadd8d200d884a85e1f4bb`
- Content digest `6ad8b07933c43b06dffe7de9cb0e582d924449b3823c17f5425ce39086edbeb9`; independent offline reference fixture, not actual API capture.

## 0185 D0 Outbox read-only projection contract
- `outbox.review.projection.schema.json` SHA-256 `96aebab7e18757e36927d45e98c4dd5a1e51fd79b8b8438d83ee9822f692c868`; backend source and frontend generated copy are byte-identical.
- Shared vectors: `product/ai-company-os-backend/tests/outbox_projection_cases.json` SHA-256 `5c835145ef738460c86ac801f0b68b70b7a5889d2fd833a3608700c2acbdb98c`. Draft 2020-12 and TypeScript parser agree on all 22 cases; no normative acceptance or runtime authority.
