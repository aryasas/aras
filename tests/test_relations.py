import os
import sys
import pytest

# Set testing environment variable for SQLite
os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///test_relations.db"

# Add api to path
sys.path.append(os.path.join(os.getcwd(), "api"))

from core import Aras
from sqlalchemy import String, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

def test_parent_child_discovery():
    # 1. Define Parent and Child models for testing
    class ParentTest(Aras.Model):
        __tablename__ = "test_parents"
        name: Mapped[str] = Aras.Column(String(50))

    class ChildTest(Aras.Model):
        __tablename__ = "test_children"
        __parent__ = "test_parents" # This should trigger auto-discovery
        name: Mapped[str] = Aras.Column(String(50))
        parent_id: Mapped[int] = Aras.Column(Integer, ForeignKey("test_parents.id"))

    # 2. Verify discovery in Model._child_map
    from core.base.model import Model
    
    assert "test_parents" in Model._child_map
    assert "test_children" in Model._child_map["test_parents"]
    
    # 3. Verify UI Metadata includes children
    metadata = ParentTest.get_ui_metadata()
    assert "test_children" in metadata["children"]
    
    print("\n[Success] Parent-Child Auto Discovery verified!")

if __name__ == "__main__":
    test_parent_child_discovery()
