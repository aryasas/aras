# Handoff Spec — Fix: Post Invoice Internal Server Error
> run_id: 8
> Written by: Claude Code (claude-sonnet-4-6)
> Date: 2026-05-18
> Feature: Fix Internal Server Error when executing Post Invoice action via Execute button

## Context
Post Invoice action via Execute button returns Internal Server Error — root cause is somewhere in the action handler chain between `router_factory.py`, `posting.py`, and `models.py`.

## Backend Tasks
- UPDATE `api/core/logic/router_factory.py` — find and fix why executing a model action causes Internal Server Error instead of surfacing the real error; trace the exception path and fix the underlying issue
- UPDATE `api/apps/erp/accounting/services/posting.py` — verify `post_inflow_invoice` and `post_outflow_invoice` return values are handled correctly by their callers in `models.py`

## Claude Review
- verdict: APPROVED
- reviewed_by: Claude Code (claude-sonnet-4-6)
- date: 2026-05-18
- notes: Both fixes verified in files. `router_factory.py` now re-raises `ArasException` preserving original error details; `InflowInvoice.post` now uses `result.get("success")` consistent with outflow. `manage.py sync` passed clean.

## Agent Reports

### Gemini Report (2026-05-18)

*   **`api/core/logic/router_factory.py`**: **FIX**
    *   Updated the exception handling for custom model actions.
    *   The previous implementation caught all `Exception` types and wrapped them in a generic `ArasException("Internal Server Error", ...)`, which hid the original error.
    *   The new implementation now specifically catches `ArasException` and re-raises it, preserving the original error details (message, status code). Other `Exception` types are still caught and wrapped as a generic internal server error. This ensures that validation errors and other specific business logic exceptions are correctly surfaced to the client.
*   **`api/apps/erp/accounting/models.py`**: **FIX**
    *   Corrected the `InflowInvoice.post` model action to properly handle the dictionary response from the `InvoicePostingService`.
    *   It now inspects the `result.get("success")` key, and on failure, raises a `ValidationException` with the specific error message from the service, consistent with the `OutflowInvoice.post` implementation. This prevents failed posting actions from appearing successful.
