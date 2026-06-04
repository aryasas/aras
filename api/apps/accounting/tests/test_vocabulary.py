from apps.accounting.org_presets import OrganizationVocabulary
from apps.accounting.services.vocabulary import apply_profile_vocabulary


# claude-opus-4-8
def test_apply_profile_vocabulary_is_idempotent(db, org):
    org.profile = "npo"
    db.flush()

    labels = apply_profile_vocabulary(db, org.id, org.profile)
    db.flush()

    rows = (
        db.query(OrganizationVocabulary)
        .filter(OrganizationVocabulary.org_id == org.id)
        .order_by(OrganizationVocabulary.key)
        .all()
    )
    assert len(rows) == 4
    assert labels["trx_in"] == "Donation"
    assert next(row for row in rows if row.key == "trx_in").label == "Donation"

    apply_profile_vocabulary(db, org.id, org.profile)
    db.flush()

    assert db.query(OrganizationVocabulary).filter(OrganizationVocabulary.org_id == org.id).count() == 4


# claude-opus-4-8
def test_get_vocabulary_resolves_profile_defaults_without_override_rows(db, auth_client, org):
    org.profile = "npo"
    db.flush()
    db.query(OrganizationVocabulary).filter(OrganizationVocabulary.org_id == org.id).delete()
    db.flush()

    resp = auth_client.get(f"/api/v1/accounting/organizations/{org.id}/vocabulary")

    assert resp.status_code == 200
    payload = resp.json()
    labels = {item["key"]: item["label"] for item in payload}
    assert labels == {
        "trx_in": "Donation",
        "trx_out": "Program Cost",
        "party": "Donor",
        "pot": "Collection Point",
    }
