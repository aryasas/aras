import pytest

def test_landing_sections_list(client, db):
    # Seed a section
    from apps.web.models import LandingSection
    section = LandingSection(key="hero", title="Welcome", body="Body text")
    db.add(section)
    db.flush()

    resp = client.get("/api/v1/web/landing")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["key"] == "hero"

def test_webpage_publish_action(auth_client, db):
    from apps.web.models import WebPage
    page = WebPage(slug="test-page", title="Test Page", content="Some content")
    db.add(page)
    db.flush()
    db.refresh(page)
    assert page.is_published is False

    # Call publish action
    resp = auth_client.post(f"/api/v1/web/page/{page.id}/action/publish")
    assert resp.status_code == 200
    
    # Verify via API fetch
    resp = auth_client.get(f"/api/v1/web/page/{page.id}")
    assert resp.status_code == 200
    assert resp.json()["data"]["is_published"] is True

