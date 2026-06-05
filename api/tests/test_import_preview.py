import io

from fastapi import UploadFile
import pytest

from apps.party.models import Party
from core.exceptions import ValidationException
from core.logic.router_factory.crud import _parse_import_file
from core.workspace.models import Organization


# gpt-5
def _make_upload_file(filename: str, content: bytes, content_type: str) -> UploadFile:
    return UploadFile(
        filename=filename,
        file=io.BytesIO(content),
        headers={"content-type": content_type},
    )


# gpt-5
def _make_xlsx_bytes(rows: list[list[object]]) -> bytes:
    openpyxl = pytest.importorskip("openpyxl")
    Workbook = openpyxl.Workbook
    workbook = Workbook()
    worksheet = workbook.active
    for row in rows:
        worksheet.append(row)
    stream = io.BytesIO()
    workbook.save(stream)
    workbook.close()
    return stream.getvalue()


# gpt-5
@pytest.fixture
def import_org(db):
    org = Organization(name="Import Org", code="IMPORT-ORG", is_default=True)
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


# gpt-5
def test_parse_import_file_supports_csv_and_xlsx_with_mapping():
    csv_bytes = b"Item Name,Role\nAcme Corp,customer\nBeta LLC,supplier\n"
    xlsx_bytes = _make_xlsx_bytes([
        ["Item Name", "Role"],
        ["Acme Corp", "customer"],
        ["Beta LLC", "supplier"],
    ])
    mapping = {"Item Name": "name", "Role": "role"}

    csv_rows = _parse_import_file(
        _make_upload_file("parties.csv", csv_bytes, "text/csv"),
        mapping,
    )
    xlsx_rows = _parse_import_file(
        _make_upload_file(
            "parties.xlsx",
            xlsx_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        mapping,
    )

    assert csv_rows == [
        {"name": "Acme Corp", "role": "customer"},
        {"name": "Beta LLC", "role": "supplier"},
    ]
    assert xlsx_rows == csv_rows


# gpt-5
def test_parse_import_file_rejects_bad_extension():
    with pytest.raises(ValidationException, match="Only CSV and XLSX files are supported"):
        _parse_import_file(
            _make_upload_file("parties.txt", b"name\nAcme\n", "text/plain"),
            None,
        )


# gpt-5
def test_import_preview_validates_rows_without_commit(auth_client, db, import_org):
    before_count = db.query(Party).count()
    csv_bytes = f"name,role,org_id\nValid Party,customer,{import_org.id}\n,supplier,{import_org.id}\n".encode()

    response = auth_client.post(
        "/api/v1/party/parties/import/preview",
        params={"mapping": "{}"},
        files={"file": ("parties.csv", csv_bytes, "text/csv")},
    )

    assert response.status_code == 200
    payload = response.json()["data"]
    assert payload["total"] == 2
    assert payload["valid"] == 1
    assert payload["invalid"] == 1
    assert payload["rows"][0]["ok"] is True
    assert payload["rows"][1]["ok"] is False
    assert payload["rows"][1]["errors"]
    assert db.query(Party).count() == before_count


# gpt-5
def test_xlsx_import_enqueues_normalized_rows(auth_client, import_org, monkeypatch):
    captured: dict[str, object] = {}
    xlsx_bytes = _make_xlsx_bytes([
        ["Party Name", "Role", "Org"],
        ["Acme Corp", "customer", import_org.id],
        ["Beta LLC", "supplier", import_org.id],
    ])

    from core.manager.task_manager import TaskManager

    def fake_enqueue_task(task_name: str, *args, **kwargs) -> str:
        captured["task_name"] = task_name
        captured["kwargs"] = kwargs
        return "task-123"

    monkeypatch.setattr(TaskManager, "enqueue_task", fake_enqueue_task)

    response = auth_client.post(
        "/api/v1/party/parties/import",
        params={"mapping": '{"Party Name":"name","Role":"role","Org":"org_id"}'},
        files={
            "file": (
                "parties.xlsx",
                xlsx_bytes,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["data"]["task_id"] == "task-123"
    assert captured["task_name"] == "task_manager.import_csv_task"
    assert captured["kwargs"]["data"] == [
        {"name": "Acme Corp", "role": "customer", "org_id": import_org.id},
        {"name": "Beta LLC", "role": "supplier", "org_id": import_org.id},
    ]
