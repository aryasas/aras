# Handoff Spec — Hierarchical Org Scope + is_shared Flag

> run_id: 11
> Written by: Claude Code (claude-sonnet-4-6)
> Date: 2026-05-18
> Feature: Hierarchical org scope expansion — parent/child data sharing + is_shared flag on master data

---

## Context

ERP scope currently filters strictly by `org_id = X`. Two use cases break:
1. Branch A needs to see items/parties/COA defined at parent HQ org
2. Office 1 accountant needs to see all branch data consolidated

Fix: expand `org_id` to a list at auth time based on org hierarchy (`is_group` flag):
- **Group org selected** (is_group=True): scope = `[group_id, child_a_id, child_b_id, ...]` — top-down, sees all descendants
- **Leaf org selected** (is_group=False): scope = `[leaf_id, parent_id, grandparent_id]` — bottom-up, sees ancestors' shared data

Writes always go to the directly selected org (first in chain).

`is_shared` flag on MasterDataBase: when False, a record is restricted to its own org only (opt-out from hierarchical sharing). Default True.

Files already read (do NOT re-read):
- `api/core/auth/service.py` — ScopeContext is built here from X-Org-ID header
- `api/core/logic/router_factory.py` — `_apply_scope_filters`, `_check_scope_ownership`, `_inject_scope_payload`
- `api/core/logic/scope.py` — ScopeContext class
- `api/core/base/model.py` — `apply_filters()` supports `in` operator: `{"field": "org_id", "op": "in", "value": [1,2,3]}`
- `api/apps/erp/base/master_data.py` — MasterDataBase with `__scoped_by__ = [("org_id", "erp_config_organizations")]`
- `api/apps/erp/config/models.py` — Organization model with `parent_id` (self-FK) and `is_group: bool`

---

## Backend Tasks

### 1. UPDATE `api/core/auth/service.py`

Find the block that reads X-Org-ID and sets `request.state.scope`. After `oid = int(request.headers.get("X-Org-ID", 0) or 0)`, replace the simple `if oid: raw["org_id"] = oid` with hierarchical expansion:

```python
oid = int(request.headers.get("X-Org-ID", 0) or 0)
if oid:
    try:
        from apps.erp.config.models import Organization

        def _get_descendants(parent_id: int) -> list[int]:
            ids = []
            children = db.query(Organization).filter(Organization.parent_id == parent_id).all()
            for c in children:
                ids.append(c.id)
                ids.extend(_get_descendants(c.id))
            return ids

        org = db.query(Organization).filter(Organization.id == oid).first()
        if org and org.is_group:
            org_chain = [oid] + _get_descendants(oid)
        elif org:
            org_chain = [oid]
            current = org
            while current and current.parent_id:
                org_chain.append(current.parent_id)
                current = db.query(Organization).filter(Organization.id == current.parent_id).first()
        else:
            org_chain = [oid]
        raw["org_id"] = org_chain if len(org_chain) > 1 else oid
    except ImportError:
        raw["org_id"] = oid
    request.state.org_id = oid  # keep direct org_id for writes
```

### 2. UPDATE `api/core/logic/router_factory.py` — 3 targeted changes

**Change A — `_apply_scope_filters`**: support list value with `in` operator + `is_shared` compound filter.

Replace the existing filter append block:
```python
for field in _scope_fields(model_class):
    val = scope.get(field)
    if val is not None and field in col_names:
        if isinstance(val, list):
            if "is_shared" in col_names:
                # Compound: own org always visible, other orgs only if is_shared=True
                direct_id = val[0]
                other_ids = val[1:]
                if other_ids:
                    parsed_filters.append({
                        "field": field,
                        "op": "shared_scope",
                        "value": {"direct": direct_id, "others": other_ids}
                    })
                else:
                    parsed_filters.append({"field": field, "op": "=", "value": direct_id})
            else:
                parsed_filters.append({"field": field, "op": "in", "value": val})
        else:
            parsed_filters.append({"field": field, "op": "=", "value": val})
```

**Change B — `_check_scope_ownership`**: handle list val:
```python
for field in _scope_fields(model_class):
    val = scope.get(field)
    if val is None:
        continue
    item_val = getattr(item, field, None)
    if isinstance(val, list):
        if item_val not in val:
            raise ResourceNotFoundException("Item not found")
    elif item_val != val:
        raise ResourceNotFoundException("Item not found")
```

**Change C — `_inject_scope_payload`**: writes always use direct org (first in chain):
```python
for field in _scope_fields(model_class):
    val = scope.get(field)
    if val is not None:
        payload[field] = val[0] if isinstance(val, list) else val
    elif not payload.get(field):
        ...  # keep existing required-field error logic unchanged
```

### 3. UPDATE `api/core/base/model.py` — support `shared_scope` filter op

In `apply_filters()` method, add handling for the `shared_scope` op alongside existing ops (`=`, `in`, `ilike`, etc.):

```python
elif op == "shared_scope" and isinstance(val, dict):
    direct_id = val["direct"]
    other_ids = val["others"]
    col_obj = getattr(cls, field)
    is_shared_col = getattr(cls, "is_shared", None)
    if is_shared_col is not None and other_ids:
        from sqlalchemy import or_
        stmt = stmt.where(
            or_(
                col_obj == direct_id,
                (col_obj.in_(other_ids)) & (is_shared_col == True)
            )
        )
    else:
        stmt = stmt.where(col_obj == direct_id)
```

### 4. UPDATE `api/apps/erp/base/master_data.py`

Add `is_shared` field to `MasterDataBase`:
```python
from sqlalchemy import Boolean
is_shared: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
```

---

## Frontend Tasks

No scope-related frontend changes needed — expansion is fully server-side.

UPDATE `ui/src/App.tsx` and add a small UX hint: when the active org is a group (`organizations.find(o => o.id === activeOrgId)?.is_group === true`), show a subtle "Consolidated View" label next to the org switcher so the user knows they're seeing all children's data. This requires `is_group` to be included in the organizations array returned by `/auth/me`.

UPDATE `ui/src/store/authStore.ts` — add `is_group?: boolean` to the `Organization` interface.

UPDATE `ui/src/layouts/MainLayout.tsx` — next to the org switcher, show a small badge:
```tsx
{activeOrganization?.is_group && (
  <span className="text-xs font-semibold text-indigo-600 bg-indigo-50 px-2 py-1 rounded-lg">
    Consolidated
  </span>
)}
```

---
<!-- ── Below this line is filled automatically by multi_agent.py + Claude ── -->

## Agent Reports (2026-05-18)

### Backend (Gemini 2.5 Flash)
- files_written: api/core/auth/service.py, api/core/logic/router_factory.py, api/core/base/model.py, api/apps/erp/base/master_data.py
- features_added: Hierarchical org scope expansion (top-down for groups, bottom-up for leaf orgs), is_shared flag on MasterDataBase to support shared data visibility.
- fixes_applied: none
- framework_changes: Enhanced RouterFactory and Model.apply_filters to handle list-based scopes and compound shared_scope filtering.
- issues: none

### Frontend (Codex GPT-5.5)
- files_written: <!-- filled by agent -->
- features_added: <!-- filled by agent -->
- fixes_applied: <!-- filled by agent -->
- framework_changes: <!-- filled by agent -->
- issues: <!-- filled by agent -->

## Claude Review
- verdict: APPROVED
- reviewed_by: Claude Code
- date: 2026-05-18
- notes: All 4 backend files match spec exactly. Frontend not yet done in this run (done in revision).

---
## Agent Reports (revision (2026-05-18))

### Backend (Gemini 2.5 Flash)
- files_written: none
- features_added: none
- fixes_applied: none
- framework_changes: none
- issues: none

### Frontend (Codex GPT-5.5)
- files_written: ui/src/store/authStore.ts, ui/src/layouts/MainLayout.tsx
- features_added: Added is_group support to Organization type and Consolidated badge beside the org switcher for group organizations
- fixes_applied: none
- framework_changes: none
- issues: none

## Claude Review
- verdict: APPROVED
- reviewed_by: Claude Code
- date: 2026-05-18
- notes: Frontend complete — authStore.ts has is_group on Organization interface, MainLayout.tsx has Consolidated badge matching spec exactly.
