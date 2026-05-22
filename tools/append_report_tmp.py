import json
from datetime import datetime

report = {
  "id": 0,
  "date": datetime.utcnow().strftime("%Y-%m-%d"),
  "feature": "Template Studio v3 (Craft.js) Backend setup",
  "revision_count": 0,
  "backend": {
    "files_written": "api/apps/dev/models.py, api/apps/dev/app.py, api/apps/dev/seed_templates.py",
    "features_added": "Extended TemplateAnnotation with Craft.js layout fields (node_id, node_kind, node_label, breakpoint, status, tree_json), added dev_api_router for /dev/dev_template_trees GET/POST and /dev/dev_template_annotations POST, seeded default erp-modern-invoice template tree JSON.",
    "fixes_applied": "Removed unique constraint on template_name so multiple annotations per template can exist.",
    "framework_changes": "none",
    "issues": "none"
  },
  "frontend": None,
  "verdict": "APPROVED"
}

with open("docs/reports.json", "r") as f:
    data = json.load(f)

report["id"] = data[-1]["id"] + 1 if data else 1
data.append(report)

with open("docs/reports.json", "w") as f:
    json.dump(data, f, indent=2)