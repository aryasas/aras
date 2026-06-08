# gemini-flash
import logging
import concurrent.futures
from datetime import date, datetime, timezone
from core import Aras
from core.lib.query_builder import QueryBuilder
from sqlalchemy.orm import Session
from sqlalchemy import func, case, and_, or_

logger = logging.getLogger(__name__)

MAX_REPORT_ROWS = 1000


class ReportService(Aras.Service):
    _BUILTIN: dict = {}

    @classmethod
    def register(cls, code: str):
        """Decorator to register a builtin report function by code."""
        def decorator(fn):
            cls._BUILTIN[code] = fn
            return fn
        return decorator

    @classmethod
    def generate(cls, report_instance, filters=None, db=None, current_user=None):
        """Execute a database-defined builtin or ORM report."""
        db = db or report_instance.db_session
        if not db:
            return {"error": "Database session not found for report instance."}

        params = {"org_id": report_instance.org_id}
        filter_defs = report_instance.filters_json or []
        if isinstance(filter_defs, list):
            for fdef in filter_defs:
                field = fdef.get("field")
                if field:
                    params[field] = fdef.get("default")
        elif isinstance(filter_defs, dict):
            params.update(filter_defs)
        if filters:
            params.update({k: v for k, v in filters.items() if v not in (None, "", "None")})

        if report_instance.report_type == "builtin":
            fn = cls._BUILTIN.get(report_instance.code)
            if not fn:
                return {"error": f"Builtin report '{report_instance.code}' not registered.", "data": [], "columns": []}
            try:
                result = fn(db=db, org_id=report_instance.org_id, params=params,
                            columns=report_instance.columns_json or [])
                result["filters_json"] = filter_defs
                return result
            except Exception as e:
                logger.exception(f"builtin report failed: {report_instance.code}")
                return {"error": str(e), "data": [], "columns": [], "filters_json": filter_defs}

        if report_instance.report_type == "orm":
            result = cls._generate_orm_report(report_instance, db, params)
        elif report_instance.report_type == "script":
            result = cls._generate_script_report(report_instance, db, params, current_user)
        else:
            return {"error": f"Report type '{report_instance.report_type}' not supported.", "data": [], "columns": []}

        result["filters_json"] = filter_defs
        return result

    @classmethod
    def _generate_script_report(cls, report, db, params, current_user):
        """Execute a Python script report with hardening."""
        # Gate behind superuser (is_admin in this framework)
        if not current_user or not getattr(current_user, "is_admin", False):
            return {"error": "403 Forbidden: Script reports require administrator privileges."}

        # Approval check
        if not report.script_approved_by_id:
            return {"error": "Report script is not approved for execution."}

        if not report.script:
            return {"error": "No script defined for this report."}

        # Whitelist globals
        safe_globals = {
            "db": db,
            "params": params,
            "result": None,
            "datetime": datetime,
            "date": date,
            "__builtins__": {} # NO __builtins__
        }

        start_time = datetime.now(timezone.utc)
        try:
            # Wrap in executor for timeout
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(exec, report.script, safe_globals)
                future.result(timeout=5) # 5s timeout
            
            result_data = safe_globals.get("result")
            duration = (datetime.now(timezone.utc) - start_time).total_seconds()
            
            # Log execution
            logger.info(f"Script report execution: user_id={current_user.id}, report_id={report.id}, duration={duration}s")
            
            if result_data is None:
                return {"error": "Script executed but 'result' variable was not set.", "data": [], "columns": report.columns_json or []}
            
            return {
                "title": report.name,
                "data": result_data if isinstance(result_data, list) else [],
                "columns": report.columns_json or []
            }
        except concurrent.futures.TimeoutError:
            logger.error(f"Script report timeout: user_id={getattr(current_user, 'id', 'unknown')}, report_id={report.id}")
            return {"error": "Script execution timed out after 5 seconds."}
        except Exception as e:
            logger.exception(f"Script report failed: {report.id}")
            return {"error": f"Script execution error: {str(e)}"}

    @classmethod
    def _generate_orm_report(cls, report, db, params):
        """Execute via ORM + QueryBuilder — no raw SQL."""
        if not report.linked_doctype:
            return {"error": "ORM report requires linked_doctype.", "data": [], "columns": []}

        model_class = Aras.Model._registry.get(report.linked_doctype)
        if not model_class:
            return {"error": f"Model {report.linked_doctype} not found.", "data": [], "columns": []}

        try:
            qb_filters = list(report.query_filters or [])
            if not any(f.get("field") == "org_id" for f in qb_filters):
                qb_filters.insert(0, {"field": "org_id", "op": "==", "value": report.org_id})

            runtime_filters = [
                {"field": k, "op": "==", "value": v}
                for k, v in params.items()
                if v not in (None, "", "None") and k not in ("org_id",)
            ]
            results = QueryBuilder.execute(db, model_class, qb_filters + runtime_filters)
            columns = report.columns_json or [
                {"field": c.name, "label": c.name} for c in model_class.__table__.columns
            ]
            data = []
            for item in results[:MAX_REPORT_ROWS]:
                row = {col["field"]: getattr(item, col["field"], None) for col in columns if "field" in col}
                data.append(row)

            return {"title": report.name, "data": data, "columns": columns}
        except Exception as e:
            logger.exception("orm report failed")
            return {"error": str(e), "data": [], "columns": []}


# ── Builtin Report Helpers ───────────────────────────────────────────

def _parse_date(val):
    if not val:
        return None
    if isinstance(val, date):
        return val
    try:
        return datetime.strptime(str(val), "%Y-%m-%d").date()
    except ValueError:
        return None
