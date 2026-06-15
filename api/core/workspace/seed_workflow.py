"""
Seed default workflow template: Invoice → Stock → Journal
Run: cd api && python -m core.workspace.seed_workflow
"""
import sys
sys.path.insert(0, ".")

from core.lib.database import SessionLocal
from core.workspace.workflow import (
    WorkflowTemplate, WorkflowState, WorkflowTransition, WorkflowAction,
)

TEMPLATES = [
    {
        "name": "Inflow Invoice Workflow",
        "document_type": "accounting_inflow_invoices",
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
                    {"handler_name": "post_stock_movement", "sequence": 10, "params": {}},
                    {"handler_name": "post_journal_entry",  "sequence": 20, "params": {}},
                ],
            },
            {
                "name": "cancel", "label": "Cancel", "icon": "XCircle",
                "from": "Draft", "to": "Cancelled", "sequence": 20, "permission": "edit",
                "actions": [],
            },
        ],
    },
    {
        "name": "Outflow Invoice Workflow",
        "document_type": "accounting_outflow_invoices",
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
                    {"handler_name": "post_stock_movement", "sequence": 10, "params": {}},
                    {"handler_name": "post_journal_entry",  "sequence": 20, "params": {}},
                ],
            },
            {
                "name": "cancel", "label": "Cancel", "icon": "XCircle",
                "from": "Draft", "to": "Cancelled", "sequence": 20, "permission": "edit",
                "actions": [],
            },
        ],
    },
    # claude-sonnet-4-6
    {
        "name": "Ticket Workflow",
        "document_type": "ticket_tickets",
        "states": [
            {"name": "Open",        "label": "Open",        "is_initial": True,  "is_final": False, "sequence": 10},
            {"name": "In Progress", "label": "In Progress", "is_initial": False, "is_final": False, "sequence": 20},
            {"name": "Resolved",    "label": "Resolved",    "is_initial": False, "is_final": True,  "sequence": 30},
            {"name": "Closed",      "label": "Closed",      "is_initial": False, "is_final": True,  "sequence": 40},
        ],
        "transitions": [
            {"name": "start",   "label": "Start Work", "icon": "Play", "from": "Open", "to": "In Progress", "sequence": 10, "permission": "edit", "actions": []},
            {"name": "resolve", "label": "Resolve",    "icon": "Check", "from": "In Progress", "to": "Resolved", "sequence": 20, "permission": "edit", "actions": []},
            {"name": "close",   "label": "Close",      "icon": "Lock", "from": "Resolved", "to": "Closed", "sequence": 30, "permission": "edit", "actions": []},
            {"name": "reopen",  "label": "Reopen",     "icon": "RefreshCw", "from": "Closed", "to": "Open", "sequence": 40, "permission": "edit", "actions": []},
        ],
    },
    # claude-sonnet-4-6
    {
        "name": "CRM Lead Workflow",
        "document_type": "crm_leads",
        "states": [
            {"name": "Lead",      "label": "Lead",      "is_initial": True,  "is_final": False, "sequence": 10},
            {"name": "Qualified", "label": "Qualified", "is_initial": False, "is_final": False, "sequence": 20},
            {"name": "Proposal",  "label": "Proposal",  "is_initial": False, "is_final": False, "sequence": 30},
            {"name": "Won",       "label": "Won",       "is_initial": False, "is_final": True,  "sequence": 40},
            {"name": "Lost",      "label": "Lost",      "is_initial": False, "is_final": True,  "sequence": 50},
        ],
        "transitions": [
            {"name": "qualify", "label": "Qualify", "icon": "UserCheck", "from": "Lead", "to": "Qualified", "sequence": 10, "permission": "edit", "actions": []},
            {"name": "propose", "label": "Proposal", "icon": "FileText", "from": "Qualified", "to": "Proposal", "sequence": 20, "permission": "edit", "actions": []},
            {"name": "win",     "label": "Won",      "icon": "Trophy", "from": "Proposal", "to": "Won", "sequence": 30, "permission": "edit", "actions": []},
            {"name": "lose",    "label": "Lost",     "icon": "Frown", "from": "Proposal", "to": "Lost", "sequence": 40, "permission": "edit", "actions": []},
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
