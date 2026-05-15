import requests
import json
import sys

def main():
    try:
        resp = requests.get("http://localhost:8000/api/v1/dev/metadata/erp_stock/erp_stock_products")
        if resp.status_code == 200:
            print(json.dumps(resp.json().get('child_tables', []), indent=2))
        else:
            print(f"Error dev: {resp.status_code}")
            resp2 = requests.get("http://localhost:8000/api/v1/erp/metadata/erp_stock/erp_stock_products")
            if resp2.status_code == 200:
                print(json.dumps(resp2.json().get('child_tables', []), indent=2))
            else:
                print("Failed both.")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    main()
