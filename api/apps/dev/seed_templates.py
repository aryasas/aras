from core import Aras
from .models import TemplateAnnotation

TEMPLATE_PRESETS = {
    "Home": [
        {"id": "hero", "name": "Hero Banner", "comment": "", "visible": True},
        {"id": "quick-actions", "name": "Quick Actions", "comment": "", "visible": True},
        {"id": "recent-activity", "name": "Recent Activity", "comment": "", "visible": True},
        {"id": "stats", "name": "Stats Cards", "comment": "", "visible": True},
    ],
    "DynamicForm": [
        {"id": "form-header", "name": "Form Header", "comment": "", "visible": True},
        {"id": "fields-area", "name": "Fields Area", "comment": "", "visible": True},
        {"id": "child-tables", "name": "Child Tables", "comment": "", "visible": True},
        {"id": "action-bar", "name": "Action Bar", "comment": "", "visible": True},
    ],
    "ListView": [
        {"id": "toolbar", "name": "Toolbar", "comment": "", "visible": True},
        {"id": "filter-bar", "name": "Filter Bar", "comment": "", "visible": True},
        {"id": "table-header", "name": "Table Header", "comment": "", "visible": True},
        {"id": "table-rows", "name": "Table Rows", "comment": "", "visible": True},
        {"id": "pagination", "name": "Pagination", "comment": "", "visible": True},
    ],
    "DevTools": [
        {"id": "tab-bar", "name": "Tab Bar", "comment": "", "visible": True},
        {"id": "overview-panel", "name": "Overview Panel", "comment": "", "visible": True},
        {"id": "handoff-panel", "name": "Handoff Panel", "comment": "", "visible": True},
    ],
    "AppManager": [
        {"id": "app-grid", "name": "App Grid", "comment": "", "visible": True},
        {"id": "app-detail", "name": "App Detail", "comment": "", "visible": True},
    ],
    "ReportCenter": [
        {"id": "filter-section", "name": "Filter Section", "comment": "", "visible": True},
        {"id": "chart-area", "name": "Chart Area", "comment": "", "visible": True},
        {"id": "table-section", "name": "Data Table", "comment": "", "visible": True},
    ],
}

ERP_MODERN_INVOICE_TREE = {
    "ROOT": {
        "type": "Box",
        "isCanvas": True,
        "props": {
            "desktop": {
                "bg": "radial-gradient(#cbd5e1 1px, transparent 1px)",
                "backgroundSize": "24px 24px",
                "direction": "row",
                "padding": "0"
            }
        },
        "displayName": "Box",
        "custom": {},
        "hidden": False,
        "nodes": [],
        "linkedNodes": {}
    }
}

def run(db):
    for name, sections in TEMPLATE_PRESETS.items():
        # Ensure order is set for backend storage
        ordered_sections = []
        for i, s in enumerate(sections):
            s_copy = s.copy()
            s_copy["order"] = i
            ordered_sections.append(s_copy)
            
        existing = db.query(TemplateAnnotation).filter_by(template_name=name).first()
        if not existing:
            ann = TemplateAnnotation(
                template_name=name,
                sections=ordered_sections,
                author="system",
                node_id="root",
                node_kind="Template",
                status="applied"
            )
            db.add(ann)
        else:
            # Optionally update if system preset changes? For now just skip.
            pass

    # Seed erp-modern-invoice with initial craft tree
    erp_invoice = db.query(TemplateAnnotation).filter_by(template_name="erp-modern-invoice").first()
    if not erp_invoice:
        ann = TemplateAnnotation(
            template_name="erp-modern-invoice",
            tree_json=ERP_MODERN_INVOICE_TREE,
            author="system",
            node_id="root",
            node_kind="TreeSnapshot",
            status="applied"
        )
        db.add(ann)

    db.commit()
