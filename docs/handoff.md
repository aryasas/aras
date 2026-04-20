# Handoff — 2026-04-20

## Completed in last session
- Created arasCore/lib/base_model.py (ArasModel + ArasSoftModel)
- Updated arasCore/lib/api_handler.py to use ArasModel methods (create, update_self, delete_self)
- Refactored all app_soc models to ArasSoftModel:
  post.py, profile.py, comment.py, friendship.py,
  conversation.py, like.py, message.py, user_pref.py

## Completed this session
Refactored all app_erp models to ArasModel/ArasSoftModel:

### erp_core/models/
- tax.py: CoreTax → ArasSoftModel, CoreTaxGroup → ArasModel, CoreTaxGroupLine → db.Model (junction)
- currency.py: CoreCurrency, CoreFxRate → ArasModel
- company.py: CoreCompany, CoreCompanyBranch → ArasModel
- fiscal.py: CoreFiscalYear, CoreFiscalPeriod → ArasModel
- sequence.py: CoreSequence → ArasModel
- setting.py: CoreSetting → kept db.Model (low-level KV store, no user context)
- report.py: ErpReport → ArasModel, ErpReportFavorite → db.Model (junction)
- notification.py: CoreNotification, CoreEmailTemplate → ArasModel
- audit.py: CoreAuditLog → kept db.Model (immutable audit trail, BigInteger PK)
- acl.py: CoreRole, CorePermission → ArasModel; CoreRolePermission, CoreUserCompany → db.Model (junction/pivot)
- attachment.py: CoreAttachment → ArasModel
- custom_field.py: CoreCustomField → ArasModel
- list_view.py: ErpListViewSetting → ArasModel
- print_template.py: CorePrintTemplate, CorePrintTemplateVersion → ArasModel

### erp_crm/models/
- customer.py: CrmCustomer → ArasSoftModel, CrmContact → ArasModel
- lead.py: CrmLead → ArasSoftModel
- pipeline.py: CrmPipeline, CrmStage → ArasModel
- activity.py: CrmActivity → ArasModel

### erp_acc/models/
- account.py: AccAccount, AccAnalyticTag → ArasModel; AccDefaultAccount → db.Model (config table)
- bank.py: AccBankStatement → ArasModel; AccBankStatementLine → db.Model (line)
- invoice.py: AccSalesInvoice, AccPurchaseInvoice → ArasModel; invoice lines → db.Model
- journal.py: AccJournal, AccJournalEntry → ArasModel; AccJournalLine → db.Model (line)
- reconciliation.py: AccReconciliation → ArasModel

### erp_stock/models/
- product.py: StockProductCategory, StockProduct → ArasModel; junction/line tables → db.Model
- uom.py: StockUomCategory, StockUom → ArasModel; StockUomConversion → db.Model
- warehouse.py: StockWarehouse, StockLocation → ArasModel
- movement.py: StockMovement → ArasModel; StockMovementLine, StockValuation → db.Model
- pricelist.py: StockPriceList → ArasModel; StockPriceListItem → db.Model

### erp_pos/models/
- terminal.py: PosTerminal, PosSession → ArasModel
- order.py: PosOrder → ArasModel; PosOrderLine, PosPayment → db.Model (lines)

## Rules applied
- Removed: id, created_at, updated_at, created_by (ArasModel provides these)
- is_active removed from most models (ArasModel provides it); kept where it conflicts with ArasModel.is_active
- Junction/pivot tables (composite PK, no timestamps) stayed db.Model
- Immutable append-only tables (CoreAuditLog) stayed db.Model
- Soft-delete: CrmCustomer, CrmLead (business entities that should never be physically deleted)
- AccAccount, AccJournalEntry use BigInteger PK — redeclared explicitly (ArasModel default is Integer)

## Next task
- Run flask aras migrate / arp-init to verify no mapper errors
- OR: write migration to handle any column changes from is_active removal / new column positions
- OR: continue with next feature

## Do NOT re-read
- arasCore/lib/base_model.py — done
- arasCore/lib/api_handler.py — done
- app_soc models — done
- app_erp/erp_core/models/* — done
- app_erp/erp_crm/models/* — done
- app_erp/erp_acc/models/* — done
- app_erp/erp_stock/models/* — done
- app_erp/erp_pos/models/* — done
