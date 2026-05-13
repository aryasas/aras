import sys
import os

# Ensure api directory is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "api")))

from core import Aras

def test_aras_structure():
    print("Testing Aras structure...")
    
    # Test lib access
    print(f"Aras.lib: {Aras.lib}")
    print(f"Aras.lib.database: {Aras.lib.database}")
    print(f"Aras.lib.database.get_db: {Aras.lib.database.get_db}")
    
    # Test helper access
    print(f"Aras.helper: {Aras.helper}")
    print(f"Aras.helper.to_snake_case('CamelCase'): {Aras.helper.to_snake_case('CamelCase')}")
    
    # Test shortcuts
    print(f"Aras.get_db: {Aras.get_db}")
    
    assert Aras.lib.database.get_db is not None
    assert Aras.helper.to_snake_case("CamelCase") == "camel_case"
    print("All tests passed!")

if __name__ == "__main__":
    test_aras_structure()
