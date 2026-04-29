import json
from arasCore.lib.core.extensions import db
from aras.erp.erp_core.models.report import ErpReport


def run_report(report_id: int, filters: dict, company_id: int = None) -> dict:
    report = ErpReport.get_or_404(report_id)
    if not report.is_active:
        return {"columns": [], "data": [], "error": "Report is inactive"}

    columns = json.loads(report.columns_json) if report.columns_json else []

    if report.report_type == "query":
        return _run_query(report, columns, filters, company_id)
    elif report.report_type == "script":
        return _run_script(report, columns, filters, company_id)
    elif report.report_type == "jinja":
        return _run_jinja(report, columns, filters, company_id)
    return {"columns": columns, "data": []}


def _run_query(report, columns, filters, company_id):
    params = dict(filters or {})
    params["company_id"] = company_id

    for f_def in (json.loads(report.filters_json) if report.filters_json else []):
        fname = f_def["field"]
        if fname not in params:
            params[fname] = None

    try:
        result = db.session.execute(db.text(report.script), params)
        keys = list(result.keys())
        rows = [list(row) for row in result.fetchall()]
        if not columns:
            columns = [{"field": k, "label": k.replace("_", " ").title(), "type": "string"} for k in keys]
        return {"columns": columns, "data": rows}
    except Exception as e:
        return {"columns": columns, "data": [], "error": str(e)}


def _run_script(report, columns, filters, company_id):
    result = {"columns": columns, "data": []}
    sandbox = {
        "db": db,
        "filters": filters or {},
        "company_id": company_id,
        "result": result,
        "json": json,
    }
    try:
        exec(report.script, sandbox)
        result = sandbox.get("result", result)
        return result
    except Exception as e:
        return {"columns": columns, "data": [], "error": str(e)}


def _run_jinja(report, columns, filters, company_id):
    from flask import current_app
    from jinja2 import Environment
    try:
        env = Environment()
        tmpl = env.from_string(report.script)
        output = tmpl.render(filters=filters or {}, company_id=company_id, db=db)
        parsed = json.loads(output)
        return parsed
    except Exception as e:
        return {"columns": columns, "data": [], "error": str(e)}
