# claude-sonnet-4-6
"""
Plugins tier (Tier 2) — opt-in shared primitives that sit between the
domain-agnostic framework (core/) and concrete products (apps/).

A plugin is reusable across many products but is not part of the framework
itself (e.g. commerce primitives: Uom, Charge, ExchangeRate, payment modes).
The framework must boot without any plugin; products opt in by depending on
one. Plugins may use core/, but never import a product (apps/).
"""
