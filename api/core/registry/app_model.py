"""
Purpose: DB model for registering installed applications.
Context: Part of Aras.Registry namespace. Maintained by SyncManager.
Impact: Acts as the primary inventory for apps accessible via the GUI.
"""
from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from ..base.model import Model

class AppModel(Model):
    """Stores metadata about installed applications."""
    __tablename__ = "aras_apps"
    __title__ = "Application Registry"

    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    label: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(255), nullable=True)
    icon: Mapped[str] = mapped_column(String(50), default="Package")
    version: Mapped[str] = mapped_column(String(20), default="1.0.0")
    config: Mapped[dict] = mapped_column(JSON, default=dict)
    is_dynamic: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)

    def delete_self(self, db: Session, user_id: int = None):
        """
        Override the generic delete_self to completely uninstall the app
        (including dropping physical tables and deleting filesystem directories)
        rather than just deleting the registry record.
        """
        from ..lib.installer import AppInstaller
        AppInstaller.uninstall_app(self.name, db)
