import os
import sys
import pytest
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped

# Add api to path
sys.path.append(os.path.join(os.getcwd(), "api"))

from core import Aras
from core.logic.ui_generator import UIGenerator
from core.lib.database import SessionLocal
from core.registry.resource_model import ResourceModel
from core.registry.link_model import LinkModel
from core.registry.app_model import AppModel

def test_db_defined_child_metadata():
    db = SessionLocal()
    try:
        # 1. Setup App and Resources
        app = AppModel(name="test_app_db", label="Test App DB")
        db.add(app)
        db.flush()

        parent_res = ResourceModel(name="db_parent", title="DB Parent", app_id=app.id, model_class="DbParent")
        child_res = ResourceModel(name="db_child", title="DB Child", app_id=app.id, model_class="DbChild")
        db.add_all([parent_res, child_res])
        db.flush()
        
        # 2. Add Child Link via DB only (not in code via __parent__)
        link = LinkModel(
            source_resource_id=parent_res.id,
            target_resource_id=child_res.id,
            field_name="lines",
            link_type="child",
            label="Lines",
            show_as_child=True
        )
        db.add(link)
        db.commit()
        
        # 3. Generate Metadata for a mock parent class
        class DbParent(Aras.Model):
            __tablename__ = "db_parent"
            
        meta = UIGenerator.generate_metadata(DbParent, db=db)
        
        # 4. Verify DB-defined child is in 'children'
        assert "db_child" in meta["children"]
        
        # 5. Verify it's also in 'fields' as 'child_table'
        child_field = next((f for f in meta["fields"] if f["name"] == "lines"), None)
        assert child_field is not None
        assert child_field["type"] == "child_table"
        assert child_field["target_resource"] == "db_child"
        
        print("\n[Success] DB-defined child metadata verified!")
        
    finally:
        # Cleanup
        db.query(LinkModel).filter(LinkModel.field_name == "lines").delete()
        db.query(ResourceModel).filter(ResourceModel.name.in_(["db_parent", "db_child"])).delete()
        db.query(AppModel).filter(AppModel.name == "test_app_db").delete()
        db.commit()
        db.close()

if __name__ == "__main__":
    test_db_defined_child_metadata()
