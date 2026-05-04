# Bugfix Requirements Document

## Introduction

The `child_table_save` endpoint in `arasCore/admin/routes/apps.py` raises a `NameError: name 'data' is not defined` when a POST request is made to save a child table row. The function builds a `raw_data` dict from the request body, but then references the undefined name `data` when iterating over the parsed payload. This causes a 500 error for all child table save operations, making the feature completely non-functional.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN a POST request is made to `/api/child-table/<model_name>/save` THEN the system raises `NameError: name 'data' is not defined` at the iteration step and returns an unhandled 500 error.

1.2 WHEN the request body is JSON THEN the system assigns the parsed payload to `raw_data` but subsequently references the undefined variable `data`, causing the function to crash before any data cleanup or persistence occurs.

1.3 WHEN the request body is form-encoded THEN the system builds `raw_data` from `request.form` but subsequently references the undefined variable `data`, causing the same crash.

### Expected Behavior (Correct)

2.1 WHEN a POST request is made to `/api/child-table/<model_name>/save` THEN the system SHALL iterate over `raw_data.items()` (the correctly assigned variable) without raising a `NameError`.

2.2 WHEN the request body is JSON THEN the system SHALL parse the payload into `raw_data`, iterate over it for cleanup, and persist the record successfully.

2.3 WHEN the request body is form-encoded THEN the system SHALL build `raw_data` from `request.form`, iterate over it for cleanup, and persist the record successfully.

### Unchanged Behavior (Regression Prevention)

3.1 WHEN a valid child table save request is made with a positive integer `item_id` THEN the system SHALL CONTINUE TO update the existing record and return `{"ok": true, "data": {...}}`.

3.2 WHEN a valid child table save request is made without an `item_id` THEN the system SHALL CONTINUE TO create a new record and return `{"ok": true, "data": {...}}`.

3.3 WHEN the `uom_id` field is present in the payload THEN the system SHALL CONTINUE TO apply the existing nullable/non-nullable validation logic for that field.

3.4 WHEN a boolean column is present in the payload THEN the system SHALL CONTINUE TO convert `"on"` to `True` and other values to `False`.

3.5 WHEN `fk_col` and `parent_id` query parameters are provided THEN the system SHALL CONTINUE TO inject the foreign key value into `raw_data` before persisting.

---

## Bug Condition

```pascal
FUNCTION isBugCondition(X)
  INPUT: X — an HTTP POST request to /api/child-table/<model_name>/save
  OUTPUT: boolean

  // The bug fires on every request because the variable name mismatch
  // is unconditional — raw_data is assigned but data is referenced.
  RETURN True
END FUNCTION
```

```pascal
// Property: Fix Checking
FOR ALL X WHERE isBugCondition(X) DO
  result ← child_table_save'(X)
  ASSERT result.status_code != 500
  ASSERT "NameError" NOT IN result.body
END FOR

// Property: Preservation Checking
FOR ALL X WHERE NOT isBugCondition(X) DO
  ASSERT child_table_save(X) = child_table_save'(X)
END FOR
```
