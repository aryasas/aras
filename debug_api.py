
from run import app
from arasCore.lib.services.api_handler import get_api_registry
from arasCore.lib.services.workflow import _workflow_registry

with app.app_context():
    api_keys = list(get_api_registry().keys())
    print("--- API REGISTRY KEYS ---")
    for k in sorted(api_keys):
        print(f"'{k}'")
    
    wf_keys = list(_workflow_registry.keys())
    print("\n--- WORKFLOW REGISTRY KEYS ---")
    for k in sorted(wf_keys):
        print(f"'{k}'")
    print("-------------------------")
