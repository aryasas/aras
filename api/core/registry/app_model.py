"""
Purpose: DB model for registering installed applications.
Context: Part of Aras.Registry namespace. Maintained by SyncManager.
Impact: Acts as the primary inventory for apps accessible via the GUI.
"""
from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column, Session
from ..base.model import Model

class AppModel(Model):
    """Stores metadata about installed applications."""
    __tablename__ = "aras_apps"

    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    parent_name: Mapped[str] = mapped_column(String(50), nullable=True, index=True)
    # app_type: "framework" = core registry owned by Aras, "app" = top-level business app, "module" = sub-app of a parent
    app_type: Mapped[str] = mapped_column(String(20), default="app")
    label: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    icon: Mapped[str] = mapped_column(String(50), default="Package")
    version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    menu_groups: Mapped[list] = mapped_column(JSON, default=list) # [{label, icon, models: []}]
    is_dynamic: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    def delete_self(self, db: Session, user_id: int = None):
        """
        Override the generic delete_self to completely uninstall the app
        (including dropping physical tables and deleting filesystem directories)
        rather than just deleting the registry record.
        """
        from ..logic.installer import AppInstaller
        AppInstaller.uninstall_app(self.name, db)
