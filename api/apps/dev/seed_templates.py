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
    "Settings": [
        {"id": "settings-nav", "name": "Settings Nav", "comment": "", "visible": True},
        {"id": "settings-form", "name": "Settings Form", "comment": "", "visible": True},
    ],
    "Profile": [
        {"id": "profile-header", "name": "Profile Header", "comment": "", "visible": True},
        {"id": "profile-details", "name": "Profile Details", "comment": "", "visible": True},
    ],
}

def create_placeholder_tree(name):
    def full_settings(padding=0, gap=16):
        spacing = {"top": padding, "right": padding, "bottom": padding, "left": padding}
        margin = {"top": 0, "right": 0, "bottom": 0, "left": 0}
        return {
            "margin": margin,
            "padding": spacing,
            "gap": gap,
            "direction": "col",
            "align": "stretch",
            "justify": "start",
            "bg": "transparent",
            "radius": 0,
            "width": None,
            "height": None
        }

    return {
        "ROOT": {
            "type": { "resolvedName": "Box" },
            "isCanvas": True,
            "props": {
                "label": f"{name} Canvas",
                "className": "w-full min-h-[600px] template-studio-dot-grid p-10 flex flex-col gap-8",
                "settings": {
                    "desktop": full_settings(40, 24),
                    "tablet": full_settings(32, 20),
                    "mobile": full_settings(24, 16)
                }
            },
            "displayName": "Box",
            "custom": {},
            "hidden": False,
            "nodes": ["header", "content"],
            "linkedNodes": {}
        },
        "header": {
            "type": { "resolvedName": "Header" },
            "props": { 
                "title": name, 
                "subtitle": "System Template", 
                "label": "Header",
                "className": "template-studio-glass",
                "settings": {
                    "desktop": full_settings(0, 16),
                    "tablet": full_settings(0, 16),
                    "mobile": full_settings(0, 16)
                }
            },
            "parent": "ROOT",
            "displayName": "Header",
            "custom": {},
            "hidden": False,
            "nodes": [],
            "linkedNodes": {}
        },
        "content": {
            "type": { "resolvedName": "Box" },
            "isCanvas": True,
            "props": { 
                "label": "Content Area", 
                "className": "flex-1 template-studio-glass rounded-[var(--aras-radius-lg)] flex items-center justify-center text-[var(--aras-muted)] font-medium",
                "settings": {
                    "desktop": full_settings(24, 16),
                    "tablet": full_settings(20, 16),
                    "mobile": full_settings(16, 12)
                }
            },
            "parent": "ROOT",
            "displayName": "Box",
            "custom": {},
            "hidden": False,
            "nodes": ["placeholder_text"],
            "linkedNodes": {}
        },
        "placeholder_text": {
            "type": { "resolvedName": "Text" },
            "props": { "text": f"Design your {name} here...", "variant": "paragraph" },
            "parent": "content",
            "displayName": "Text",
            "custom": {},
            "hidden": False,
            "nodes": [],
            "linkedNodes": {}
        }
    }

ERP_MODERN_INVOICE_TREE = {
    "ROOT": {
        "type": { "resolvedName": "Box" },
        "isCanvas": True,
        "props": {
            "className": "template-studio-dot-grid w-full",
            "settings": {
                "desktop": {
                    "direction": "row",
                    "padding": { "top": 24, "right": 24, "bottom": 24, "left": 24 },
                    "gap": 24,
                }
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
                tree_json=create_placeholder_tree(name),
                author="system",
                node_id="root",
                node_kind="Template",
                status="applied"
            )
            db.add(ann)
        elif not existing.tree_json:
            existing.tree_json = create_placeholder_tree(name)
    
    # Seed erp-modern-invoice with initial craft tree if it doesn't exist
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
