# -*- coding: utf-8 -*-
"""
arasCore/lib/middleware/
========================
Middleware layer for the Aras framework.

Pipeline: raw input → AppMiddleware → installer/registry → Flask app

Current middleware modules:
  app_definition.py  — normalizes app definition dicts (YAML/JSON/Python)
  python_loader.py   — handles Python file/zip upload → module injection

Future extension points:
  - AI-assisted field inference (e.g. natural language → schema)
  - Format adapters (e.g. Odoo XML, Django fixture, custom DSL)
  - Validation plugins
  - Pre/post install hooks
"""
from .app_definition import AppDefinitionMiddleware
from .python_loader import PythonLoaderMiddleware

__all__ = ["AppDefinitionMiddleware", "PythonLoaderMiddleware"]
