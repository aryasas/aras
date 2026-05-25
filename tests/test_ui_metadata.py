import os
import sys

# Add api to path
sys.path.append(os.path.join(os.getcwd(), "api"))

from datetime import datetime, date
from core import Aras
from sqlalchemy import String, Integer, Float, Boolean, DateTime, Date, Enum, ForeignKey
from sqlalchemy.orm import Mapped

class MockModel(Aras.Model):
    __tablename__ = "mock_model"

    name: Mapped[str] = Aras.Column(String(100), label="Name")
    is_true: Mapped[bool] = Aras.Column(Boolean)
    count: Mapped[int] = Aras.Column(Integer)
    price: Mapped[float] = Aras.Column(Float)
    created: Mapped[datetime] = Aras.Column(DateTime)
    today: Mapped[date] = Aras.Column(Date)
    status: Mapped[str] = Aras.Column(Enum("Draft", "Active", "Closed", name="mock_status"))
    # Re-target FK to a table that exists post-erp-removal.
    other_id: Mapped[int] = Aras.Column(Integer, ForeignKey("aras_apps.id"))

def test_smart_metadata_detection():
    meta = MockModel.get_ui_metadata()
    fields = {f["name"]: f for f in meta["fields"]}
    
    print(f"Detected types: {[ (f['name'], f['type']) for f in meta['fields'] ]}")
    
    assert fields["name"]["type"] == "string"
    assert fields["is_true"]["type"] == "boolean"
    assert fields["count"]["type"] == "number"
    assert fields["price"]["type"] == "number"
    assert fields["created"]["type"] == "datetime"
    assert fields["today"]["type"] == "date"
    assert fields["status"]["type"] == "select"
    assert len(fields["status"]["options"]) == 3
    assert fields["other_id"]["type"] == "lookup"
    # Can be 'aras_apps' or '/dev/aras-apps' depending on if Dev app is registered
    assert fields["other_id"]["target_resource"] in ("aras_apps", "dev/aras-apps", "/dev/aras-apps")

if __name__ == "__main__":
    try:
        test_smart_metadata_detection()
        print("UI Metadata Detection Test Passed!")
    except Exception as e:
        print(f"Test Failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
