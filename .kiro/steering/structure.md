# Project Structure

## Top-Level Layout

```
arasCore/          # Framework engine — do not modify unless explicitly asked
aras/              # Pluggable business applications
templates/         # Global Jinja2 templates (admin, auth, layouts)
static/            # CSS, JS, fonts, images
tests/             # pytest test suite
config.py          # Flask config (dev/test/prod)
app.py             # App factory entry point
run.py             # Dev server launcher
requirements.txt   # Python dependencies
app_install.yaml   # Declarative app definitions (YAML-based installs)
```

## arasCore/ — Framework Engine

```
arasCore/
  lib/
    core/
      base_model.py      # ArasModel and ArasSoftModel base classes
    services/
      app_helper.py      # AppHelper, ResourceDef, MenuGroup
      api_handler.py     # Auto REST API registration
      installer.py       # App installation logic
      schema_migrator.py # DB migration engine
      events.py          # Event/webhook system
      search.py          # Global search
      workflow.py        # State machine engine
  admin/
    crud_factory.py      # Auto CRUD UI generation
    routes.py            # Admin blueprint routes
    services.py          # Sidebar, form builder
  auth.py                # Flask-Login + RBAC
  permissions.py         # Role/permission definitions
  forms.py               # Base form classes
```

## aras/ — Business Applications

Each app follows this structure:

```
aras/<app_name>/
  manifest.py            # App registration (Python-based apps)
  <module>/
    models/              # SQLAlchemy models
    services/            # Business logic
    views/               # Optional custom views
    templates/<module>/  # Optional templates (fallback to admin defaults)
```

### ERP Sub-modules

```
aras/erp/
  erp_acc/    # Accounting: accounts, invoices, journals, payments, reconciliation
  erp_core/   # Shared ERP: company, currency, tax, fiscal year, sequences, settings
  erp_crm/    # CRM: customers, leads, contacts
  erp_pos/    # Point of Sale: terminals, shifts, sessions
  erp_stock/  # Inventory: products, warehouses, stock moves, UoM
  erp_hr/     # HR: employees, departments, payroll
```

## Naming Conventions

| Artifact | Convention | Example |
|---|---|---|
| DB table | `<module>_<entity>` | `acc_account`, `pos_terminal` |
| Model class | PascalCase with prefix | `AccAccount`, `PosTerminal` |
| DB columns | snake_case | `legal_name`, `parent_id` |
| Foreign keys | `<entity>_id` | `company_id`, `parent_id` |
| Boolean fields | `is_*` or `enable_*` | `is_group`, `enable_perpetual_inventory` |
| Files/modules | snake_case | `payment_service.py` |

## Model Conventions

- All models inherit from `ArasModel` (or `ArasSoftModel` for soft-delete)
- Define `__display_fields__` tuple for search/dropdown display
- Use `before_save(is_new)` and `after_save(is_new)` hooks for business logic
- Use `SubHandler` class for custom CRUD handler logic
- Audit columns (`created_at`, `updated_at`, `created_by`, `updated_by`) are auto-added
- Unique constraints go in `__table_args__`
- Always use absolute imports (`from aras.erp...`, `from arasCore...`)

## Templates

- Global admin templates: `templates/admin/`
- App-specific templates: `aras/<app>/templates/<module>/`
- Max 2 templates per page type: `<type>_form.html` (create) and `<type>_detail.html` (read/update/delete)
- If no app template exists, the framework falls back to admin defaults

## Tests

```
tests/
  client.py          # Custom test client wrapper
  fixtures/          # YAML/JSON app definitions for test installs
  test_auth/
  test_admin/
  test_appmanager/
  test_erp/
```
