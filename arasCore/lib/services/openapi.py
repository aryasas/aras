# -*- coding: utf-8 -*-
"""
arasCore/lib/services/openapi.py
===============================
OpenAPI Spec generator for Aras Universal API.
Converts _api_registry models and _custom_route_registry into OpenAPI 3.0.
"""
import logging
from flask import current_app

logger = logging.getLogger(__name__)

def generate_openapi_spec():
    from arasCore.lib.services.api_handler import get_api_registry, _custom_route_registry
    from arasCore.admin.models import AppManagerTable, AppManagerColumn
    from sqlalchemy import inspect
    
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "Aras Framework API",
            "version": "1.0.0",
            "description": "Auto-generated OpenAPI documentation for Aras Universal API"
        },
        "servers": [
            {"url": "/api", "description": "Base API Path"}
        ],
        "components": {
            "schemas": {},
            "securitySchemes": {
                "cookieAuth": {
                    "type": "apiKey",
                    "in": "cookie",
                    "name": "session"
                }
            }
        },
        "security": [
            {"cookieAuth": []}
        ],
        "paths": {}
    }

    registry = get_api_registry()
    
    # Cache AppManagerColumn info for all models
    table_configs = {}
    try:
        tables = AppManagerTable.query.all()
        for tbl in tables:
            cols = AppManagerColumn.query.filter_by(table_id=tbl.id).all()
            table_configs[tbl.db_table_name] = cols
    except Exception as e:
        logger.warning(f"[openapi] Could not fetch AppManagerColumn configs: {e}")

    for key, entry in registry.items():
        model = entry["model"]
        schema_name = model.__name__
        
        # 1. Build Schema
        if schema_name not in spec["components"]["schemas"]:
            spec["components"]["schemas"][schema_name] = _model_to_schema(model, table_configs.get(model.__tablename__, []))

        # 2. Build Paths (Collection & Item)
        res_path = f"/{key}/"
        item_path = f"/{key}/{{id}}/"
        
        # Collection Paths
        spec["paths"][res_path] = {
            "get": {
                "tags": [key.split("/")[0]],
                "summary": f"List {schema_name}",
                "parameters": [
                    {"name": "page", "in": "query", "schema": {"type": "integer", "default": 1}},
                    {"name": "per_page", "in": "query", "schema": {"type": "integer", "default": 50}},
                    {"name": "q", "in": "query", "schema": {"type": "string"}, "description": "Search query"},
                    {"name": "sort", "in": "query", "schema": {"type": "string"}, "description": "Sort field (prefix with - for desc)"},
                    {"name": "format", "in": "query", "schema": {"type": "string", "enum": ["json", "csv"]}}
                ],
                "responses": {
                    "200": {
                        "description": "List of items",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "data": {"type": "array", "items": {"$ref": f"#/components/schemas/{schema_name}"}},
                                        "meta": {"type": "object"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        if not entry.get("readonly"):
            spec["paths"][res_path]["post"] = {
                "tags": [key.split("/")[0]],
                "summary": f"Create {schema_name}",
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {"$ref": f"#/components/schemas/{schema_name}"}
                        }
                    }
                },
                "responses": {
                    "201": {"description": "Created", "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{schema_name}"}}}},
                    "422": {"description": "Validation Error"}
                }
            }
            
            # Item Paths
            spec["paths"][item_path] = {
                "get": {
                    "tags": [key.split("/")[0]],
                    "summary": f"Get {schema_name} by ID",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                    "responses": {
                        "200": {"description": "Success", "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{schema_name}"}}}},
                        "404": {"description": "Not Found"}
                    }
                },
                "put": {
                    "tags": [key.split("/")[0]],
                    "summary": f"Update {schema_name}",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/{schema_name}"}
                            }
                        }
                    },
                    "responses": {
                        "200": {"description": "Updated", "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{schema_name}"}}}},
                        "422": {"description": "Validation Error"}
                    }
                },
                "delete": {
                    "tags": [key.split("/")[0]],
                    "summary": f"Delete {schema_name}",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                    "responses": {
                        "200": {"description": "Deleted"},
                        "404": {"description": "Not Found"}
                    }
                }
            }
        else:
             spec["paths"][item_path] = {
                "get": {
                    "tags": [key.split("/")[0]],
                    "summary": f"Get {schema_name} by ID",
                    "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "integer"}}],
                    "responses": {
                        "200": {"description": "Success", "content": {"application/json": {"schema": {"$ref": f"#/components/schemas/{schema_name}"}}}}
                    }
                }
             }

    # 3. Custom Routes
    for path, creg in _custom_route_registry.items():
        full_path = f"/{path}/"
        # basic path param conversion <int:id> -> {id}
        import re
        swagger_path = re.sub(r"<(?:int:)?(\w+)>", r"{\1}", full_path)
        
        path_params = re.findall(r"<(?:int:)?(\w+)>", full_path)
        
        methods = [m.lower() for m in creg["methods"]]
        if swagger_path not in spec["paths"]:
            spec["paths"][swagger_path] = {}
        
        for m in methods:
            spec["paths"][swagger_path][m] = {
                "tags": ["Custom"],
                "summary": f"Custom route: {path}",
                "parameters": [
                    {"name": p, "in": "path", "required": True, "schema": {"type": "string"}} 
                    for p in path_params
                ],
                "responses": {
                    "200": {"description": "Success"}
                }
            }

    return spec

def _model_to_schema(model, am_cols):
    """Convert SQLAlchemy model + AppManagerColumns into JSON Schema."""
    properties = {}
    required = []
    
    # Map from AppManagerColumn
    col_map = {c.name: c for c in am_cols}
    
    for col in model.__table__.columns:
        name = col.name
        am_col = col_map.get(name)
        
        prop = {}
        sql_type = str(col.type.__class__.__name__).lower()
        
        if "integer" in sql_type:
            prop["type"] = "integer"
        elif "numeric" in sql_type or "float" in sql_type or "decimal" in sql_type:
            prop["type"] = "number"
        elif "boolean" in sql_type:
            prop["type"] = "boolean"
        elif "datetime" in sql_type or "date" in sql_type:
            prop["type"] = "string"
            prop["format"] = "date-time" if "datetime" in sql_type else "date"
        else:
            prop["type"] = "string"

        # Apply AppManagerColumn constraints
        if am_col:
            if am_col.label:
                prop["title"] = am_col.label
            if am_col.required:
                required.append(name)
            if am_col.max_length:
                prop["maxLength"] = am_col.max_length
            if am_col.min_value is not None:
                prop["minimum"] = float(am_col.min_value)
            if am_col.max_value is not None:
                prop["maximum"] = float(am_col.max_value)
            if am_col.regex_pattern:
                prop["pattern"] = am_col.regex_pattern
        else:
            if not col.nullable and not col.primary_key and col.default is None:
                required.append(name)

        properties[name] = prop

    schema = {
        "type": "object",
        "properties": properties
    }
    if required:
        schema["required"] = required
        
    return schema
