from core.lib.i18n import seed_locale_translations
from core.registry.translation_model import TranslationModel


def test_public_i18n_bundle_endpoint_returns_locale_strings(client):
    response = client.get("/api/v1/i18n/id.json")

    assert response.status_code == 200
    data = response.json()
    assert data["nav.dashboard"] == "Dasbor"
    assert data["lang.label"] == "Bahasa"
    assert data["public.signup.title"] == "Daftar ARAS"


def test_locale_seed_is_idempotent(db):
    first = seed_locale_translations(db)
    second = seed_locale_translations(db)

    assert first["inserted"] + first["updated"] > 0
    assert second["inserted"] == 0
    assert second["updated"] == 0

    rows = db.query(TranslationModel).filter(TranslationModel.registry_type == "locale").all()
    assert rows
    assert any(row.language_code == "id" and row.property_name == "nav.dashboard" for row in rows)
