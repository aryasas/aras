# -*- coding: utf-8 -*-
"""
arasCore/lib/middleware/app_definition.py
=========================================
AppDefinitionMiddleware — normalizes app definition input before it reaches
the installer/registry.

Entry points:
  from_yaml(content: bytes) -> dict
  from_json(content: bytes) -> dict
  from_dict(data: dict)     -> dict
  from_file(file_storage)   -> dict   (detects format by filename)

All methods return a normalized definition dict compatible with
arasCore.lib.installer.parse_app_definition().

Future extension:
  - from_ai(prompt: str)     → call Claude/LLM to generate definition
  - from_odoo_xml(content)   → parse Odoo module XML
  - from_django(content)     → parse Django model file
  - from_dsl(content)        → custom Aras DSL syntax
  - validate(definition)     → pluggable validation hooks
"""
import json
import logging
import yaml

logger = logging.getLogger(__name__)


class AppDefinitionMiddleware:
    """
    Thin normalization layer between raw input formats and the installer.
    Currently passes through to arasCore.lib.installer.parse_app_definition().
    """

    @staticmethod
    def from_yaml(content: bytes) -> dict:
        """Parse YAML bytes → normalized definition dict."""
        try:
            data = yaml.safe_load(content)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")
        return AppDefinitionMiddleware._normalize(data)

    @staticmethod
    def from_json(content: bytes) -> dict:
        """Parse JSON bytes → normalized definition dict."""
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
        return AppDefinitionMiddleware._normalize(data)

    @staticmethod
    def from_dict(data: dict) -> dict:
        """Pass a plain dict → normalized definition dict."""
        return AppDefinitionMiddleware._normalize(data)

    @staticmethod
    def from_file(file_storage) -> dict:
        """
        Auto-detect format from FileStorage filename, parse and normalize.
        Supports .yaml, .yml, .json, and .zip (zip must contain a definition file).
        Raises ValueError on unknown format or parse error.
        """
        filename = (file_storage.filename or "").lower()

        if filename.endswith(".zip"):
            return AppDefinitionMiddleware.from_zip(file_storage)

        content = file_storage.read()
        if filename.endswith((".yaml", ".yml")):
            return AppDefinitionMiddleware.from_yaml(content)
        elif filename.endswith(".json"):
            return AppDefinitionMiddleware.from_json(content)
        else:
            raise ValueError("Only .yaml, .yml, .json, or .zip files are accepted.")

    @staticmethod
    def from_zip(file_storage) -> dict:
        """
        Extract a zip and find the first YAML/JSON definition file inside.
        Searches zip root and one level deep.
        Raises ValueError if no definition file found.
        """
        import zipfile, io

        content = file_storage.read() if hasattr(file_storage, "read") else file_storage
        try:
            zf = zipfile.ZipFile(io.BytesIO(content))
        except zipfile.BadZipFile:
            raise ValueError("Invalid zip file.")

        # Prefer manifest.yaml > manifest.yml > manifest.json > any *.yaml > *.json
        names = zf.namelist()
        priority = ["manifest.yaml", "manifest.yml", "manifest.json"]

        def _basename(n):
            return n.split("/")[-1].lower()

        def _find(candidates):
            for p in candidates:
                for n in names:
                    if _basename(n) == p and not n.endswith("/"):
                        return n
            return None

        match = _find(priority)
        if not match:
            # fallback: first .yaml/.yml/.json at root or one level deep
            for n in names:
                parts = [p for p in n.split("/") if p]
                if len(parts) <= 2 and _basename(n).endswith((".yaml", ".yml", ".json")):
                    match = n
                    break

        if not match:
            raise ValueError(
                "Zip must contain a definition file (.yaml/.yml/.json) — "
                "e.g. manifest.yaml at the root or inside one subfolder."
            )

        def_bytes = zf.read(match)
        zf.close()
        logger.info(f"[app_definition] loading definition from zip entry: {match}")

        if match.lower().endswith(".json"):
            return AppDefinitionMiddleware.from_json(def_bytes)
        return AppDefinitionMiddleware.from_yaml(def_bytes)

    @staticmethod
    def _normalize(data: dict) -> dict:
        """
        Core normalization pipeline.
        Currently delegates to installer.parse_app_definition().
        Insert pre/post processing hooks here as the framework evolves.
        """
        from arasCore.lib.installer import parse_app_definition

        # Pre-processing hook (placeholder)
        data = AppDefinitionMiddleware._pre_process(data)

        # Parse & validate
        definition = parse_app_definition(data)

        # Post-processing hook (placeholder)
        definition = AppDefinitionMiddleware._post_process(definition)

        return definition

    @staticmethod
    def _pre_process(data: dict) -> dict:
        """
        Pre-processing hook — runs before parse_app_definition().
        Future: format adapters, AI-generated schema expansion, etc.
        """
        return data

    @staticmethod
    def _post_process(definition: dict) -> dict:
        """
        Post-processing hook — runs after parse_app_definition().
        Future: default field injection, audit column appending, etc.
        """
        return definition
