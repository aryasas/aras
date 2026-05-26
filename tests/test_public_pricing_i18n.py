import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_PLAN_KEYS = {"free", "lite", "growth", "business"}
PUBLIC_TRANSLATION_KEYS = {
    "public.nav.pricing",
    "public.nav.login",
    "public.nav.tryFree",
    "public.hero.badge",
    "public.hero.titleTop",
    "public.hero.titleAccent",
    "public.hero.description",
    "public.hero.primary",
    "public.hero.secondary",
    "public.pricing.title",
    "public.pricing.subtitle",
    "public.pricing.free",
    "public.pricing.perMonth",
    "public.pricing.popular",
    "public.pricing.startFree",
    "public.pricing.startNow",
    "public.signup.title",
    "public.signup.subtitle",
    "public.signup.fullName",
    "public.signup.email",
    "public.signup.company",
    "public.signup.phone",
    "public.signup.plan",
    "public.signup.submit",
    "public.signup.successTitle",
}


def test_public_pricing_and_signup_use_current_public_plan_keys():
    landing = (ROOT / "ui/src/views/PublicLanding.tsx").read_text()
    signup = (ROOT / "ui/src/views/CustomerSignup.tsx").read_text()

    for source in (landing, signup):
        for key in PUBLIC_PLAN_KEYS:
            assert f"'{key}'" in source
        assert "'starter'" not in source
        assert "'enterprise'" not in source

    assert "to={`/signup?plan=${plan.plan_key}`}" in landing
    assert "searchParams.get('plan')" in signup
    assert "plans.find((p) => p.plan_key === form.plan_key)" in signup


def test_public_pricing_and_signup_have_en_id_translations():
    en = json.loads((ROOT / "ui/src/locales/en.json").read_text())
    id_ = json.loads((ROOT / "ui/src/locales/id.json").read_text())

    missing_en = sorted(PUBLIC_TRANSLATION_KEYS - set(en))
    missing_id = sorted(PUBLIC_TRANSLATION_KEYS - set(id_))

    assert missing_en == []
    assert missing_id == []
