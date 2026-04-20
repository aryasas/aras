# ERP_11 — Build Plan & Roadmap

Phased delivery, optimized untuk UKM 5-20 user. Tiap fase = MVP deliverable yg
bisa dipakai user real (no big-bang).

---

## 0. Konvensi Repo

```
aras/
  app_core/        # ERP_01
  app_acc/         # ERP_05  (build sebelum SAL/PUR/HRP butuh posting)
  app_inv/         # ERP_02
  app_sal/         # ERP_03
  app_pur/         # ERP_04
  app_hrp/         # ERP_06
  app_sho/         # ERP_07
  app_cms/         # ERP_08
  app_manager/     # existing low-code (untuk custom field & block)
  lib/
    scoping.py     # company multi-tenant query scope
    audit.py       # SQLAlchemy event hook
    extras.py      # custom field overlay helper
    money.py       # Decimal helpers, rounding
    events.py      # blinker signals
    print_engine.py
docs/erp/          # this folder
migrations/        # alembic
tests/
  test_<module>_*  # mirror app structure
```

---

## Phase 0 — Foundation (Week 1–2)

**Goal:** infra ready untuk multi-company + sequence + audit + custom field.

Deliverable:
- [ ] `app_core` skeleton (blueprint + base models di §2,3,4,7,8 of ERP_01).
- [ ] `core_company`, `core_currency`, `core_user_company`, `core_role`, `core_permission`, `core_setting`, `core_sequence`.
- [ ] Multi-tenant query scoping (`g.current_company_id` + SQLAlchemy hook).
- [ ] Permission decorator `@require_perm`.
- [ ] Audit log infrastructure.
- [ ] `core_attachment` + storage backend abstraction.
- [ ] `core_custom_field` + extras helper.
- [ ] Print engine (`core_print_template`) + WeasyPrint.
- [ ] Company switcher di header admin.
- [ ] Seed: default company, IDR currency, SUPERADMIN role, sequences.
- [ ] CLI: `flask aras erp-init` (run all seeds).

Tests:
- Multi-tenant isolation (user A company X tidak lihat data company Y).
- Sequence concurrency (10 thread → no duplicate).
- Custom field render + save + validate.

---

## Phase 1 — Accounting Core (Week 3–4)

**Goal:** ledger ready, jurnal manual bisa diposting.

Deliverable:
- [ ] `acc_account` + COA template loader (`id_psak_basic`, `id_umkm`).
- [ ] `acc_default_account` mapping.
- [ ] `acc_journal`, `acc_journal_entry`, `acc_journal_line`.
- [ ] `acc_analytic_tag`.
- [ ] `core_fiscal_year`, `core_fiscal_period` + open/close UI.
- [ ] `core_tax`, `core_tax_group` + `core.tax.compute()`.
- [ ] `acc.posting.post_journal()` service (atomic, balanced check).
- [ ] Manual JV form (admin).
- [ ] Reports: Trial Balance, GL, Balance Sheet, P&L.
- [ ] Currency FX rate + `core.fx.convert()`.
- [ ] Reverse entry mechanism.
- [ ] Permission seeds.

Tests:
- Posting balanced enforcement.
- Period lock blocks posting.
- COA tree integrity (no cycle).
- Tax compute (inclusive / exclusive / compound).
- Trial Balance debit==credit.

---

## Phase 2 — Inventory (Week 5–6)

Deliverable:
- [ ] `inv_uom`, `inv_category`, `inv_product` (+ images, variants stub).
- [ ] `inv_warehouse`, `inv_location`.
- [ ] `inv_move`, `inv_move_line`, `inv_stock_quant`.
- [ ] `inv_valuation_layer` + FIFO consume.
- [ ] AVG costing alternative.
- [ ] Stock adjustment workflow.
- [ ] Lot/serial (basic).
- [ ] Reorder cron (Celery).
- [ ] Reports: Stock Card, Valuation, Reorder, Slow-mover.
- [ ] Posting hooks → ACC (Inventory + GR/IR for receipt; COGS for delivery).

Tests:
- FIFO valuation correctness.
- Negative stock prevention.
- Cross-warehouse transfer no valuation change.
- Adjustment journal posting.

---

## Phase 3 — Purchasing (Week 7–8)

Deliverable:
- [ ] `pur_vendor`, `pur_vendor_pricelist`.
- [ ] `pur_request` (optional flow).
- [ ] `pur_order` + lines, RFQ → PO.
- [ ] Auto-generate `inv_move` (receipt) on PO confirm.
- [ ] `pur_bill` + lines, 3-way match.
- [ ] `pur_payment` + allocation + reconciliation.
- [ ] `pur_landed_cost` (basic by_qty).
- [ ] Withholding tax handling.
- [ ] Print: PO, Bill, Payment Voucher.

Tests:
- 3-way match rejects mismatched bill.
- Bill with PPN+PPh posts correctly.
- Landed cost adjusts valuation_layer.

---

## Phase 4 — Sales & Invoicing (Week 9–10)

Deliverable:
- [ ] `sal_customer`, `sal_pricelist` + price resolver.
- [ ] `sal_order` (Quotation → SO) + delivery generation.
- [ ] `sal_invoice` (from SO + standalone) + state machine.
- [ ] Credit limit check + approval matrix integration.
- [ ] `sal_payment` + allocation + reconciliation.
- [ ] Credit note mechanism.
- [ ] Withholding handled.
- [ ] Email send on confirm + due reminders cron.
- [ ] Print: Quotation, Invoice (A4 + thermal + e-faktur), Receipt.

Tests:
- SO → delivery → invoice → payment full cycle posts correct journals.
- Credit limit blocks confirm.
- Reminder cron picks correct invoices.

---

## Phase 5 — HR & Payroll (Week 11–12)

Deliverable:
- [ ] `hrp_department`, `hrp_job_position`, `hrp_employee`, `hrp_contract`.
- [ ] `hrp_work_schedule`, `hrp_attendance` (manual + clock-in API).
- [ ] `hrp_leave_type`, `hrp_leave_request`, `hrp_leave_balance` + approval flow.
- [ ] `hrp_salary_structure` + `hrp_salary_rule` + simpleeval sandbox.
- [ ] `hrp_payslip`, `hrp_payroll_run` batch.
- [ ] PPh 21 rules (Indonesia) sebagai sample structure.
- [ ] Posting payslip → ACC.
- [ ] Bank transfer batch CSV export.
- [ ] Print: payslip, contract.

Tests:
- Salary expression sandbox (no arbitrary code exec).
- Payslip totals = sum lines, debit==credit on posting.
- Leave balance deduction correct.

---

## Phase 6 — CMS Frontend (Week 13–14)

Deliverable:
- [ ] `cms_site`, `cms_theme`, `cms_page`, `cms_block`, `cms_block_type`.
- [ ] Built-in block types (15+ from ERP_08 §2.4).
- [ ] Page editor (drag-drop + live preview iframe).
- [ ] `cms_menu`, `cms_menu_item`, `cms_contact_info`.
- [ ] `cms_form` + submissions + reCAPTCHA.
- [ ] `cms_legal_doc`, `cms_redirect`, `cms_banner`.
- [ ] Theme tokens + CSS variables injection.
- [ ] Public router (/, /<slug>) + caching.
- [ ] SEO (sitemap, robots, OG, structured data).
- [ ] Multi-locale support.
- [ ] Custom block via app_manager integration.
- [ ] Seed: default site + 8 default pages.

Tests:
- Page render with all built-in blocks.
- Cache invalidation on publish.
- Form submission validation + email + reCAPTCHA.
- Multi-locale fallback.

---

## Phase 7 — Online Store (Week 15–17)

Deliverable:
- [ ] `sho_customer_account` + auth (register, login, verify, reset).
- [ ] `sho_address`.
- [ ] Storefront pages: catalog, category, product detail (CMS + product data).
- [ ] `sho_cart` (guest session + DB-persisted).
- [ ] `sho_wishlist`.
- [ ] Checkout flow (4 steps).
- [ ] `sho_shipping_method` (manual + flat + by_weight; carrier APIs as plug).
- [ ] `sho_payment_method` + at least 1 gateway integration (Midtrans atau Xendit).
- [ ] `sho_payment_transaction` + webhook handler.
- [ ] `sho_order` lifecycle + auto-create SAL pipeline on paid.
- [ ] `sho_shipment` + tracking display.
- [ ] `sho_coupon` + apply at checkout.
- [ ] `sho_review` (post-delivery).
- [ ] Customer area `/me/*`.
- [ ] Email templates (10+).
- [ ] Stock reservation + TTL release.
- [ ] Cart abandonment recovery.

Tests:
- Full guest checkout → paid → SO → invoice → COGS.
- Logged-in checkout uses saved address.
- Webhook signature validation.
- Stock reservation prevents overselling.
- Coupon usage limits enforced.

---

## Phase 8 — Polish & Production Readiness (Week 18+)

- [ ] OpenAPI doc generation.
- [ ] Webhook outbound delivery (`core_webhook` + retry).
- [ ] API token management UI.
- [ ] `core_approval_rule` engine.
- [ ] Holiday & working hours (HR + SLA).
- [ ] Backup CLI + cron.
- [ ] Performance: query indexes audit, N+1 cleanup, cache layer.
- [ ] Security: rate limit, CSRF on storefront, password policy, 2FA opsional admin.
- [ ] i18n complete (id, en).
- [ ] User docs + video.
- [ ] Migration tool from spreadsheet (CSV import wizard per master).

---

## Cross-Cutting Definition of Done (per phase)

Setiap modul belum "done" sampai:
1. Models + migration (Alembic).
2. Permissions seeded.
3. Sequences seeded (jika applicable).
4. CRUD UI lengkap (list/create/edit/detail/delete).
5. State actions tersedia (button + API).
6. Print template default tersedia.
7. Email template default (jika applicable).
8. REST API conform `ERP_09`.
9. Test coverage ≥ 70% pada service & posting.
10. Doc updated di `ERP_NN_*.md` jika ada perubahan schema.
11. CLI seed command working.

---

## Risk & Mitigation

| Risk | Mitigation |
|------|------------|
| Posting bug korup ledger | Strict: only `acc.posting`; tests; audit log; reverse-only correction |
| Multi-tenant leak | SQLAlchemy global filter + integration test per query |
| FIFO / costing race | DB row lock on valuation_layer |
| Payment double-post | Idempotency key + gateway_ref UNIQUE |
| Custom field bloat | JSON column (no schema explosion); index only when needed |
| Print template XSS | Jinja autoescape ON; sandboxed env; whitelist filters |
| Salary rule code injection | `simpleeval` only; no `eval`/`exec` |
| Storefront DDoS | Rate limit + Redis cache + CDN (CloudFlare) recommended |
| Period reopen abuse | Audit + permission `acc.period.reopen` SUPERADMIN only |

---

## Next Action

1. Review semua `ERP_*.md` bersama stakeholder.
2. Confirm COA template default (PSAK basic vs UMKM).
3. Confirm tax codes (PPN 11%, PPh codes yg dipakai).
4. Confirm payment gateway pilihan (Midtrans / Xendit / both).
5. Mulai **Phase 0** — buat branch `feature/erp-foundation`, generate migration, seed.
