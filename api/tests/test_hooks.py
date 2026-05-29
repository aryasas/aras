# claude-opus-4-7
"""Verify Backend 15: on_validate decorator + db/user_id injection into lifecycle hooks."""
import pytest
from sqlalchemy import Column, String

from core.base.aras import Aras
from core.base.model import Model
from core.exceptions import ValidationException


class HookProbe(Model):
    __tablename__ = "test_hook_probe"
    __abstract__ = False

    name = Column(String(50))

    calls: list = []

    @Aras.on_validate
    def _v(self, db=None, user_id=None):
        type(self).calls.append(("validate", db is not None, user_id))
        if self.name == "BLOCK":
            raise ValidationException("blocked by validator")

    @Aras.on_create
    def _c(self, db=None, user_id=None):
        type(self).calls.append(("create", db is not None, user_id))

    @Aras.on_update
    def _u(self, db=None, user_id=None):
        type(self).calls.append(("update", db is not None, user_id))

    @Aras.on_delete
    def _d(self, db=None, user_id=None):
        type(self).calls.append(("delete", db is not None, user_id))


@pytest.fixture(autouse=True)
def _reset_calls():
    HookProbe.calls = []
    yield


@pytest.fixture
def probe_table(db_engine):
    HookProbe.__table__.create(bind=db_engine, checkfirst=True)
    yield
    HookProbe.__table__.drop(bind=db_engine, checkfirst=True)


def test_on_create_receives_db_and_user_id(db, probe_table):
    HookProbe.create(db, {"name": "alice"}, user_id=42)
    assert ("validate", True, 42) in HookProbe.calls
    assert ("create", True, 42) in HookProbe.calls
    assert not any(c[0] == "update" for c in HookProbe.calls)


def test_on_update_receives_db_and_user_id(db, probe_table):
    obj = HookProbe.create(db, {"name": "bob"}, user_id=1)
    HookProbe.calls = []
    obj.update_self(db, {"name": "bob2"}, user_id=99)
    assert ("validate", True, 99) in HookProbe.calls
    assert ("update", True, 99) in HookProbe.calls


def test_on_validate_aborts_save(db, probe_table):
    with pytest.raises(ValidationException):
        HookProbe.create(db, {"name": "BLOCK"}, user_id=7)
    assert not any(c[0] == "create" for c in HookProbe.calls)


def test_on_delete_receives_db_and_user_id(db, probe_table):
    obj = HookProbe.create(db, {"name": "carol"}, user_id=1)
    HookProbe.calls = []
    obj.delete_self(db, user_id=55)
    assert ("delete", True, 55) in HookProbe.calls
