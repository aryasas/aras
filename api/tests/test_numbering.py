# gemini-flash
import pytest
import threading
from sqlalchemy.orm import Session
from core.lib.numbering import numbering
from core.lib.config import config
from core.registry.config_registry import config_registry, ConfigSection, ConfigField

def test_numbering_basic(db: Session):
    config_registry.clear()
    section = ConfigSection(
        key="core_config.numbering",
        label="Numbering",
        fields=[ConfigField(key="invoice", type="string", default="INV-{year}-{seq:4}")]
    )
    config_registry.register_section("core_config", section)
    
    num1 = numbering.next(db, "invoice")
    assert num1.startswith("INV-202")
    assert num1.endswith("0001")
    
    num2 = numbering.next(db, "invoice")
    assert num2.endswith("0002")

def test_numbering_custom_format(db: Session):
    config_registry.clear()
    section = ConfigSection(
        key="core_config.numbering",
        label="Numbering",
        fields=[ConfigField(key="order", type="string", default="ORD-{MM}/{DD}/{seq}")]
    )
    config_registry.register_section("core_config", section)
    
    num = numbering.next(db, "order")
    assert num.startswith("ORD-")
    # ORD-05/29/1 etc.
    assert "/" in num

def test_numbering_concurrency(db: Session):
    config_registry.clear()
    section = ConfigSection(
        key="core_config.numbering",
        label="Numbering",
        fields=[ConfigField(key="threaded", type="string", default="{seq}")]
    )
    config_registry.register_section("core_config", section)
    db.commit()

    results = []
    def get_next():
        from core.lib.database import SessionLocal
        local_db = SessionLocal()
        try:
            num = numbering.next(local_db, "threaded")
            results.append(num)
            local_db.commit()
        finally:
            local_db.close()

    threads = [threading.Thread(target=get_next) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
        
    assert len(results) == 10
    assert len(set(results)) == 10 # All unique
