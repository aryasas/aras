from apps.accounting.services.vocabulary import apply_profile_vocabulary
from apps.accounting.reports import _sales_summary


# claude-opus-4-8
def test_sales_summary_title_uses_resolved_npo_vocabulary(db, org):
    org.profile = "npo"
    db.flush()
    apply_profile_vocabulary(db, org.id, org.profile)
    db.flush()

    result = _sales_summary(db, org.id, {}, [])

    assert "Donation" in result["title"]
    assert "Sales" not in result["title"]
