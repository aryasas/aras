from core.api.dashboard import _ensure_trade_default_layout
from core.auth.models import User
from core.registry.app_model import AppModel
from core.registry.dashboard_layout_model import DashboardLayoutModel
from core.registry.widget_model import TRADE_APP_NAMES, TRADE_WIDGET_DEFINITIONS, WidgetModel


# claude-opus-4-8
def _create_app_rows(db, names: set[str]) -> None:
    for name in names:
        existing = db.query(AppModel).filter(AppModel.name == name).first()
        if existing:
            existing.is_active = True
            continue
        db.add(AppModel(
            name=name,
            label=name.title(),
            description=f"{name} app",
            icon="Package",
            version="1.0.0",
            is_active=True,
        ))
    db.flush()


# claude-opus-4-8
def _create_user(db, username: str) -> User:
    user = User(
        username=username,
        email=f"{username}@aras.local",
        password_hash=User.hash_password("password123"),
        is_admin=True,
    )
    db.add(user)
    db.flush()
    db.refresh(user)
    return user


# claude-opus-4-8
def test_trade_widgets_seed_idempotently_and_default_layout_stable(db, org):
    _create_app_rows(db, set(TRADE_APP_NAMES))

    WidgetModel.seed_defaults(db)
    first_count = db.query(WidgetModel).filter(WidgetModel.name.like("trade_%")).count()
    WidgetModel.seed_defaults(db)
    second_count = db.query(WidgetModel).filter(WidgetModel.name.like("trade_%")).count()

    expected_names = [definition["name"] for definition in TRADE_WIDGET_DEFINITIONS]
    rows = db.query(WidgetModel).filter(WidgetModel.name.in_(expected_names)).all()
    assert first_count == len(expected_names)
    assert second_count == len(expected_names)
    assert sorted(row.name for row in rows) == sorted(expected_names)
    assert all(row.widget_type in {"trade_kpi", "trade_list"} for row in rows)
    assert all(row.resource_name == "report/dashboard" for row in rows)
    assert all(row.app_id is not None for row in rows)

    user = _create_user(db, "trade_layout_user")
    layout_first = _ensure_trade_default_layout(db, user, org.id)
    layout_second = _ensure_trade_default_layout(db, user, org.id)

    assert layout_first is not None
    assert layout_second is not None
    assert layout_first.id == layout_second.id

    layouts = db.query(DashboardLayoutModel).filter(
        DashboardLayoutModel.user_id == user.id,
        DashboardLayoutModel.is_default == True,
    ).all()
    assert len(layouts) == 1
    widget_names = [widget["name"] for widget in layouts[0].layout_config["widgets"]]
    assert widget_names == expected_names


# claude-opus-4-8
def test_dashboard_widgets_returns_trade_layout_for_trade_org_user(client, db, org, auth_headers):
    _create_app_rows(db, set(TRADE_APP_NAMES))
    WidgetModel.seed_defaults(db)

    user = _create_user(db, "trade_dashboard_user")
    client.headers.update(auth_headers(user))

    response = client.get("/api/v1/dashboard/widgets", headers={"X-Org-ID": str(org.id)})
    assert response.status_code == 200

    payload = response.json()
    widgets = payload["layout_config"]["widgets"]
    assert payload["is_default"] is True
    assert {widget["widget_type"] for widget in widgets} == {"trade_kpi", "trade_list"}
    assert [widget["name"] for widget in widgets] == [definition["name"] for definition in TRADE_WIDGET_DEFINITIONS]


# claude-opus-4-8
def test_non_trade_org_keeps_generic_default_widgets(client, db, org, auth_headers, monkeypatch):
    WidgetModel.seed_defaults(db)
    user = _create_user(db, "generic_dashboard_user")
    client.headers.update(auth_headers(user))

    monkeypatch.setattr(WidgetModel, "is_trade_org", classmethod(lambda cls, db, org_id=None, installed_app_names=None: False))

    response = client.get("/api/v1/dashboard/widgets", headers={"X-Org-ID": str(org.id)})
    assert response.status_code == 200

    payload = response.json()
    widgets = payload["layout_config"]["widgets"]
    assert payload["is_default"] is False
    assert all(widget["widget_type"] != "trade_kpi" for widget in widgets)
    assert all(widget["widget_type"] != "trade_list" for widget in widgets)
    assert "trade_today_sales" not in {widget["name"] for widget in widgets}


# claude-opus-4-8
def test_non_trade_profile_org_is_generic_even_with_trade_apps(db, org):
    """An NGO-profile org must NOT get the trade dashboard even where trade apps are
    installed globally — the per-org profile denylist overrides the installed-apps check."""
    org.profile = "npo"
    db.flush()
    assert WidgetModel.is_trade_org(db, org_id=org.id, installed_app_names=set(TRADE_APP_NAMES)) is False
    names = {d["name"] for d in WidgetModel.get_default_widget_payloads(db, org_id=org.id)}
    assert not any(n.startswith("trade_") for n in names)

    org.profile = "company"
    db.flush()
    assert WidgetModel.is_trade_org(db, org_id=org.id, installed_app_names=set(TRADE_APP_NAMES)) is True
