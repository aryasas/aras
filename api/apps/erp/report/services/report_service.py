from core import Aras
from core.lib.query_builder import QueryBuilder
from sqlalchemy.orm import Session, object_session
from sqlalchemy import text

class ReportService(Aras.Service):
    @classmethod
    def generate(cls, report_instance, filters=None):
        """
        Executes the report based on its type.
        """
        db = object_session(report_instance)
        if not db:
            return {"error": "Database session not found for report instance."}

        # 1. Start with default params
        params = {"org_id": report_instance.org_id}
        
        # 2. Extract default values from filter definitions (if any)
        # In Aras, filters_json is often a list of definitions: [{"field": "x", "default": "y"}]
        filter_defs = report_instance.filters_json or []
        if isinstance(filter_defs, list):
            for fdef in filter_defs:
                field = fdef.get("field")
                if field:
                    params[field] = fdef.get("default")
        elif isinstance(filter_defs, dict):
            params.update(filter_defs)

        # 3. Override with provided filters from the UI
        if filters:
            params.update(filters)

        # 4. Ensure null for common filters if not provided (prevents SQL parameter missing errors)
        common_params = ["date_from", "date_to", "status", "customer", "vendor"]
        for p in common_params:
            if p not in params:
                params[p] = None

        if report_instance.report_type == "query":
            return cls._generate_query_report(report_instance, db, params)
        elif report_instance.report_type == "script":
            return cls._generate_script_report(report_instance, db, params)
        else:
            return {
                "error": f"Report type {report_instance.report_type} not supported yet.",
                "data": [],
                "columns": []
            }

    @classmethod
    def _generate_query_report(cls, report, db, filters):
        # 1. If raw SQL script is provided, execute it
        if report.script and report.script.strip().upper().startswith("SELECT"):
            try:
                params = {"org_id": report.org_id}
                params.update(filters)
                
                result = db.execute(text(report.script), params)
                columns = [{"field": k, "label": k.replace("_", " ").title()} for k in result.keys()]
                
                # If report has predefined columns_json, use those labels
                if report.columns_json:
                    col_map = {c["field"]: c["label"] for c in report.columns_json}
                    for col in columns:
                        if col["field"] in col_map:
                            col["label"] = col_map[col["field"]]

                data = [dict(row._mapping) for row in result]
                return {
                    "title": report.name,
                    "data": data,
                    "columns": report.columns_json or columns
                }
            except Exception as e:
                return {
                    "error": f"SQL Error: {str(e)}",
                    "data": [],
                    "columns": []
                }

        # 2. Fallback to QueryBuilder if linked_doctype exists
        if report.linked_doctype:
            model_class = Aras.Model._registry.get(report.linked_doctype)
            if not model_class:
                return {"error": f"Model {report.linked_doctype} not found.", "data": [], "columns": []}
            
            # QueryBuilder expects a list of filter dicts, but we have a single dict here
            # We'll convert our filters dict to QueryBuilder format for simplicity
            qb_filters = [{"field": k, "op": "==", "value": v} for k, v in filters.items() if v]
            
            results = QueryBuilder.execute(db, model_class, qb_filters)
            data = []
            columns = report.columns_json or []
            
            for item in results:
                row = {}
                if columns:
                    for col in columns:
                        field = col.get("field")
                        row[field] = getattr(item, field, None)
                else:
                    for column in model_class.__table__.columns:
                        row[column.name] = getattr(item, column.name, None)
                data.append(row)
                
            return {
                "title": report.name,
                "data": data,
                "columns": columns or [{"field": c.name, "label": c.name} for c in model_class.__table__.columns]
            }

        return {
            "error": "Query report requires either a SQL script or a linked_doctype.",
            "data": [],
            "columns": []
        }

    @classmethod
    def _generate_script_report(cls, report, db, filters):
        if not report.script:
            return {"error": "Script report has no content.", "data": [], "columns": []}

        # Prepare context for the script
        from core.lib.db import db as db_wrapper
        result_dict = {"data": [], "columns": []}
        
        # Use a single namespace for both globals and locals to ensure
        # that variables defined in the script (like date_from) are available
        # throughout the script's execution.
        ctx = {
            "db": db_wrapper, 
            "org_id": report.org_id,
            "filters": filters,
            "result": result_dict
        }
        
        try:
            # Execute the script
            exec(report.script, ctx, ctx)
            
            # The script should have populated result_dict or updated local variables
            # In seeded reports, they use result["data"] and result["columns"]
            return {
                "title": report.name,
                "data": result_dict.get("data", []),
                "columns": result_dict.get("columns", [])
            }
        except Exception as e:
            return {
                "error": f"Script Error: {str(e)}",
                "data": [],
                "columns": []
            }
