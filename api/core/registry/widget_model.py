from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship
from ..base.model import Model

class WidgetModel(Model):
    """
    Registry for Dashboard Widgets.
    Widgets can be Stats, Charts, or Recent Activity lists.
    """
    __tablename__ = "aras_widgets"
    __title__ = "Dashboard Widget"

    name = Column(String(100), nullable=False)
    title = Column(String(100), nullable=False)
    widget_type = Column(String(50), nullable=False) # stat, chart, list
    resource_name = Column(String(100), nullable=True) # Data source
    config_json = Column(JSON, nullable=True) # Options like color, icon, query filters
    size = Column(String(20), default="col-span-1") # UI layout hint
    order = Column(Integer, default=0)
    
    # Optional: Link to a specific App
    app_id = Column(Integer, ForeignKey("aras_apps.id", ondelete="CASCADE"), nullable=True)
    app = relationship("AppModel", backref="widgets")

    @classmethod
    def get_default_widgets(cls, db):
        """Returns standard widgets if none configured."""
        return db.query(cls).order_by(cls.order).all()
