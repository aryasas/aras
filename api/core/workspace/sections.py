# gemini-flash
from core.registry.config_registry import ConfigSection, ConfigField

# Two kinds of organization configuration exist in Aras, and neither lives here as a
# user-facing config section:
#
#   1. Per-org / per-branch data (name, currency, fiscal year, tax_id, logo, addresses)
#      is owned by the multi-row `core_organizations` model — edited at
#      /core-config/core-organizations. Single source of truth.
#
#   2. Instance-wide preferences (SMTP, branding, localization defaults, i18n, integrations)
#      are owned by the `core` namespace (see core/registry/core_sections.py) — edited in the
#      settings hub at /admin/settings. Single source of truth.
#
# This module therefore only registers two INTERNAL sections that must keep the legacy
# `core_config` namespace because their keys are referenced as string literals across the
# codebase (numbering.py, seeds/base.py, tests). Both are hidden from the settings hub.

core_config_sections = [
    ConfigSection(
        key="core_config.numbering",
        label="Numbering",
        icon="Hash",
        order=30,
        scope="shared",
        level="system",
        hidden=True,
        dynamic=True,  # keys are document series seeded from seeds/series.yaml at runtime
        fields=[]
    ),
    ConfigSection(
        key="core_config.menu",
        label="Menu Order",
        order=999,
        scope="core",
        level="system",
        hidden=True,
        fields=[
            ConfigField(key="order", type="list", default=[], label="Menu Order")
        ]
    ),
]

# Back-compat alias: some imports may still reference `sections`.
sections = core_config_sections


# claude-opus-4-8
# Register at import time (mirrors core/registry/core_sections.py) so that any consumer
# writing to a core_config.* key sees the section regardless of app-sync ordering.
# Idempotent: config_registry is keyed by section.key.
def register_workspace_sections() -> None:
    from core.registry.config_registry import config_registry
    for section in core_config_sections:
        config_registry.register_section("core_config", section)


register_workspace_sections()
