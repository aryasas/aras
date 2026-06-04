def test_registry_populated_by_inverted_hooks(client):
    from core.service_registry import ServiceRegistry
    for k in ["JournalService", "Organization", "Item", "Product", "LicenseService",
              "get_access", "get_user_org_list", "StockComputeService", "Notification", "Subscription"]:
        assert ServiceRegistry.get(k) is not None, f"{k} MISSING from registry"
