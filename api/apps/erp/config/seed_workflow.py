"""
Seed default workflow template: Invoice → Stock → Journal
Run: cd api && python -m apps.erp.config.seed_workflow
"""
import sys
sys.path.insert(0, ".")

from core.lib.database import SessionLocal
from apps.erp.config.workflow_models import (
    WorkflowTemplate, WorkflowState, WorkflowTransition, WorkflowAction,
)

TEMPLATES = [
    {
        "name": "Sales Invoice Workflow",
        "document_type": "erp_accounting_sales_invoices",
        "states": [
            {"name": "Draft",     "label": "Draft",     "is_initial": True,  "is_final": False, "sequence": 10},
            {"name": "Posted",    "label": "Posted",    "is_initial": False, "is_final": True,  "sequence": 20},
            {"name": "Cancelled", "label": "Cancelled", "is_initial": False, "is_final": True,  "sequence": 30},
        ],
        "transitions": [
            {
                "name": "post", "label": "Post", "icon": "Send",
                "from": "Draft", "to": "Posted", "sequence": 10, "permission": "edit",
                "actions": [
                    {"handler_name": "post_stock_movement", "sequence": 10,
                     "params": {"move_type": "Outgoing", "location_field": "location_id"}},
                    {"handler_name": "post_journal_entry", "sequence": 20,
                     "params": {"mode": "cogs", "use_product_category_accounts": True}},
                ],
            },
            {
                "name": "cancel", "label": "Cancel", "icon": "XCircle",
                "from": "Draft", "to": "Cancelled", "sequence": 20, "permission": "edit",
                "actions": [],
            },
        ],
    },
]


def run():
    db = SessionLocal()
    try:
        for tpl_data in TEMPLATES:
            existing = db.query(WorkflowTemplate).filter_by(
                document_type=tpl_data["document_type"]
            ).first()
            if existing:
                print(f"[SKIP] Template already exists: {tpl_data['name']}")
                continue

            tpl = WorkflowTemplate(
                name=tpl_data["name"],
                document_type=tpl_data["document_type"],
                is_active=True,
            )
            db.add(tpl)
            db.flush()

            state_map = {}
            for s in tpl_data["states"]:
                state = WorkflowState(
                    template_id=tpl.id,
                    name=s["name"], label=s["label"],
                    is_initial=s["is_initial"], is_final=s["is_final"],
                    sequence=s["sequence"],
                )
                db.add(state)
                db.flush()
                state_map[s["name"]] = state.id

            for t in tpl_data["transitions"]:
                trans = WorkflowTransition(
                    template_id=tpl.id,
                    from_state_id=state_map[t["from"]],
                    to_state_id=state_map[t["to"]],
                    name=t["name"], label=t["label"], icon=t["icon"],
                    permission=t.get("permission"),
                    sequence=t["sequence"],
                )
                db.add(trans)
                db.flush()

                for a in t["actions"]:
                    db.add(WorkflowAction(
                        transition_id=trans.id,
                        handler_name=a["handler_name"],
                        params=a["params"],
                        sequence=a["sequence"],
                    ))

            db.commit()
            print(f"[OK] Seeded: {tpl_data['name']}")

    finally:
        db.close()

    print("Done.")


if __name__ == "__main__":
    run()
