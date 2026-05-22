with open("docs/handoff.md", "a") as f:
    f.write("\n## Backend Implementation Report\n")
    f.write("- **Updated `api/apps/dev/models.py`**: Extended `TemplateAnnotation` with `node_id`, `node_kind`, `node_label`, `breakpoint`, `status`, `comment`, and `tree_json`. Dropped `unique=True` on `template_name`.\n")
    f.write("- **Updated `api/apps/dev/app.py`**: Added `dev_api_router` with endpoints `GET /dev/dev_template_trees`, `POST /dev/dev_template_trees`, and `POST /dev/dev_template_annotations`.\n")
    f.write("- **Updated `api/apps/dev/seed_templates.py`**: Seeded default `erp-modern-invoice` template tree JSON.\n")
    f.write("- **Migration**: Ran `python api/manage.py sync` (Aras framework handles missing columns natively, no Alembic required).\n")
    f.write("- **Reporting**: Report appended to `docs/reports.json`.\n")

with open("docs/feature.md", "a") as f:
    f.write("\n## Template Studio v3 (Craft.js) (2026-05-22)\n")
    f.write("- **Backend**: Extended `TemplateAnnotation` model, added `/dev_template_trees` and `/dev_template_annotations` endpoints, seeded default `erp-modern-invoice` tree, synced schema.\n")
