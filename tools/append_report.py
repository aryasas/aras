import json

with open('docs/reports.json', 'r') as f:
    reports = json.load(f)

new_id = reports[-1]['id'] + 1 if reports else 1

new_report = {
  "id": new_id,
  "date": "2026-05-19",
  "feature": "POS fixes + Tenant Admin UI",
  "revision_count": 0,
  "backend": {
    "files_written": "api/apps/erp/pot/services/pot.py, api/apps/erp/pot/models.py",
    "features_added": "none",
    "fixes_applied": "Fixed PotService stale imports and SQLAlchemy 2.0 db.get() usage. Restored PotSession.orders relationship.",
    "framework_changes": "none",
    "issues": "none"
  },
  "frontend": {
    "files_written": "ui/src/views/TenantAdmin.tsx, ui/src/App.tsx, ui/src/views/PosView.tsx",
    "features_added": "TenantAdmin page with provisioning and seeding actions. Added receipt panel in POS view.",
    "fixes_applied": "none",
    "framework_changes": "none",
    "issues": "none"
  },
  "verdict": "APPROVED"
}

reports.append(new_report)

with open('docs/reports.json', 'w') as f:
    json.dump(reports, f, indent=2)
