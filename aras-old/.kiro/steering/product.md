# Product: Aras Framework

Aras is a modular, metadata-driven ERP and application framework built on Flask and SQLAlchemy. It is conceptually similar to ERPNext but simpler — apps are defined via Python manifests or YAML/JSON, and the framework auto-generates REST APIs, admin CRUD interfaces, and RBAC controls from those definitions.

## Core Purpose
- Provide a pluggable app registry where business applications can be installed and managed
- Auto-generate REST APIs and admin UI from app/model definitions
- Enforce RBAC, audit trails, workflow states, and multi-tenancy across all apps

## Key Modules
- **arasCore** — The framework engine (not to be modified unless explicitly asked)
- **aras/erp** — Full ERP suite: accounting (`erp_acc`), CRM (`erp_crm`), POS (`erp_pos`), stock/inventory (`erp_stock`), HR (`erp_hr`)
- **aras/soc** — Social/community app (example)
- **aras/todo** — Minimal example app

## Framework Features
- Dynamic app registry (install via YAML/JSON or Python manifest)
- Universal auto-generated REST API (`/api/<app>/<resource>/`)
- Auto-generated admin CRUD UI (`/admin/<app>/<resource>/`)
- Declarative workflow engine with RBAC-gated state transitions
- Server-side scripting hooks (`before_save`, `after_save`)
- Global command-palette search
- Webhooks and event system
- Field-level audit trail
- CLI tools via `flask aras <command>`
