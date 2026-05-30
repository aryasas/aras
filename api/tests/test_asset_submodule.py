import pytest

def test_asset_submodule_dependency():
    from core.base.app import App
    asset_app = next((a for a in App._registry.values() if a.app_name == "accounting.assets"), None)
    assert asset_app is not None
    assert asset_app.parent_name == "accounting"
    assert "accounting" in asset_app.requires
