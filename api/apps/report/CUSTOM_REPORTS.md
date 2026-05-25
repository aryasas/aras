# Custom Reports — Safe Builtin & ORM Reports

All reports are stored in the `Report` model. Python `exec()`, raw SQL strings, and
custom SQL execution are disabled.

## Report Types

### Builtin Reports (`report_type: "builtin"`)

Use this for curated reports implemented in backend code and registered by code:

```python
@ReportService.register("stock_summary")
def _stock_summary(db, org_id, params, columns):
    ...
```

The database row controls visibility, labels, module grouping, filters, and columns.
The backend function controls the query.

### ORM Reports (`report_type: "orm"`)

Use this for user-configurable reports. The user chooses a model, columns, and
structured filters. The backend builds SQLAlchemy queries from whitelisted fields.

```json
{
  "code": "customer_sales",
  "name": "Customer Sales Report",
  "report_type": "orm",
  "linked_doctype": "InflowInvoice",
  "query_filters": [
    {"field": "status", "op": "==", "value": "Posted"}
  ],
  "columns_json": [
    {"field": "number", "label": "Invoice"},
    {"field": "total_amount", "label": "Total", "type": "currency"}
  ],
  "filters_json": [
    {"field": "date_from", "label": "Date From", "type": "date"}
  ]
}
```

## Security Rules

- Reports always execute inside a validated organization context.
- `org_id` query parameters are validated against the authenticated user's access.
- Raw SQL and Python script reports are rejected by the model.
- `/api/v1/report/execute/{report_code}` is the canonical execution endpoint.

## API

```http
GET /api/v1/report/execute/{report_code}?field1=value1
```

Response:

```json
{
  "data": [{ "...": "..." }],
  "columns": [{ "field": "x", "label": "X" }],
  "title": "Report Name",
  "filters_json": []
}
```
