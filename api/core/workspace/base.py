# claude-opus-4-8
"""Workspace ORM bases — thin aliases over the canonical core bases.

The real definitions live in core/base/orm.py (framework tier, shared by all
apps/plugins). Workspace models historically referenced WorkspaceConfigBase /
WorkspaceMasterDataBase, so we keep those names as aliases.
"""
from core.base.orm import ConfigBase as WorkspaceConfigBase
from core.base.orm import MasterDataBase as WorkspaceMasterDataBase

__all__ = ["WorkspaceConfigBase", "WorkspaceMasterDataBase"]
