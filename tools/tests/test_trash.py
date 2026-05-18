import urllib.request
import urllib.parse
import json
import base64
import os

BASE_URL = "http://0.0.0.0:8000/api/v1"
USERNAME = "admin"
PASSWORD = "admin"
ORG_ID = "1"

def make_request(method, url, headers=None, data=None, json_payload=False):
    if headers is None:
        headers = {}

    req = urllib.request.Request(url, method=method, headers=headers)

    if data:
        if json_payload:
            data = json.dumps(data).encode('utf-8')
            req.add_header('Content-Type', 'application/json')
        else:
            data = urllib.parse.urlencode(data).encode('utf-8')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')

    try:
        with urllib.request.urlopen(req, data=data) as response:
            response_body = response.read().decode('utf-8')
            return json.loads(response_body)
    except urllib.error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        if e.fp:
            error_details = e.fp.read().decode('utf-8')
            try:
                print(f"Error Details: {json.loads(error_details)}")
            except json.JSONDecodeError:
                print(f"Error Details: {error_details}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

def main():
    test_results = {"auth": False, "list_deleted_initial": False, "create_item": False,
                    "delete_item_initial": False, "restore_item": False,
                    "verify_restore": False, "delete_item_final": False,
                    "verify_delete_final": False}
    overall_pass = True

    print("--- Starting Aras ERP API Soft-Delete/Restore Test ---")

    # 1. Authenticate
    print("\n1. Authenticating...")
    token_url = f"{BASE_URL}/auth/token"
    auth_data = {"username": USERNAME, "password": PASSWORD}
    auth_response = make_request("POST", token_url, data=auth_data)

    if auth_response:
        if auth_response.get("success"):
            access_token = auth_response["data"]["access_token"]
        elif "access_token" in auth_response:
            access_token = auth_response["access_token"]
        else:
            print(f"Authentication failed: Unexpected response format: {auth_response}")
            overall_pass = False
            print("--- Test Finished: FAIL ---")
            return
            
        auth_headers = {"Authorization": f"Bearer {access_token}", "X-Org-ID": ORG_ID}
        print("Authentication successful. Access Token obtained.")
        test_results["auth"] = True
    else:
        print("Authentication failed.")
        overall_pass = False
        print("--- Test Finished: FAIL ---")
        return

    # 2. List deleted items (initial)
    print("\n2. Listing initially deleted stock items...")
    deleted_items_url = f"{BASE_URL}/erp/stock/items/deleted"
    deleted_response_initial = make_request("GET", deleted_items_url, headers=auth_headers)

    initial_deleted_count = 0
    item_to_test_id = None

    if deleted_response_initial and deleted_response_initial.get("success"):
        data = deleted_response_initial["data"]
        if isinstance(data, dict) and "items" in data:
            initial_deleted_items = data["items"]
        else:
            initial_deleted_items = data
            
        initial_deleted_count = len(initial_deleted_items)
        print(f"Initial deleted items count: {initial_deleted_count}")
        for item in initial_deleted_items:
            print(f"  ID: {item.get('id')}, Name: {item.get('name')}, Org ID: {item.get('org_id')}")
        test_results["list_deleted_initial"] = True

        if initial_deleted_count > 0:
            item_to_test_id = initial_deleted_items[0]["id"]
            print(f"Found existing deleted item to test: {item_to_test_id}")
    else:
        print("Failed to list initially deleted items.")
        overall_pass = False

    # 3. Create and delete a test item if no deleted item exists
    if not item_to_test_id:
        print("\n3. No deleted item found. Creating a new item for testing...")
        create_item_url = f"{BASE_URL}/erp/stock/items"
        new_item_data = {"name": "Test Item for Soft-Delete", "org_id": int(ORG_ID), "description": "This is a temporary item for soft-delete testing."}
        create_response = make_request("POST", create_item_url, headers=auth_headers, data=new_item_data, json_payload=True)

        if create_response and create_response.get("success"):
            item_to_test_id = create_response["data"]["id"]
            print(f"New item created with ID: {item_to_test_id}")
            test_results["create_item"] = True

            print(f"Soft-deleting newly created item {item_to_test_id}...")
            delete_item_url = f"{BASE_URL}/erp/stock/items/{item_to_test_id}"
            delete_response = make_request("DELETE", delete_item_url, headers=auth_headers)

            if delete_response and delete_response.get("success"):
                print(f"Item {item_to_test_id} soft-deleted successfully.")
                test_results["delete_item_initial"] = True
            else:
                print(f"Failed to soft-delete item {item_to_test_id} after creation.")
                overall_pass = False
        else:
            print("Failed to create new item for testing.")
            overall_pass = False

    if not item_to_test_id:
        print("No item ID to test. Cannot proceed.")
        overall_pass = False

    if overall_pass:
        # 4. Restore the item
        print(f"\n4. Restoring item with ID: {item_to_test_id}...")
        restore_url = f"{BASE_URL}/erp/stock/items/{item_to_test_id}/restore"
        # POST with empty JSON body, as per typical REST restore endpoints
        restore_response = make_request("POST", restore_url, headers=auth_headers, data={}, json_payload=True)

        if restore_response and restore_response.get("success"):
            print(f"Restore response message: {restore_response.get('message')}")
            test_results["restore_item"] = True
        else:
            print(f"Failed to restore item {item_to_test_id}.")
            overall_pass = False

    if overall_pass:
        # 5. Verify restoration
        print(f"\n5. Verifying item {item_to_test_id} is now in the live list...")
        live_items_url = f"{BASE_URL}/erp/stock/items"
        live_response = make_request("GET", live_items_url, headers=auth_headers)

        item_found_live = False
        if live_response and live_response.get("success"):
            data = live_response["data"]
            items = data["items"] if isinstance(data, dict) and "items" in data else data
            for item in items:
                if item.get("id") == item_to_test_id:
                    item_found_live = True
                    break
            if item_found_live:
                print(f"PASS: Item {item_to_test_id} found in live list after restoration.")
                test_results["verify_restore"] = True
            else:
                print(f"FAIL: Item {item_to_test_id} NOT found in live list after restoration.")
                overall_pass = False
        else:
            print("Failed to get live items list.")
            overall_pass = False

    if overall_pass:
        # 6. Soft-delete it again to restore test state
        print(f"\n6. Soft-deleting item {item_to_test_id} again to restore test state...")
        delete_item_url = f"{BASE_URL}/erp/stock/items/{item_to_test_id}"
        delete_response_final = make_request("DELETE", delete_item_url, headers=auth_headers)

        if delete_response_final and delete_response_final.get("success"):
            print(f"Item {item_to_test_id} soft-deleted successfully (final).")
            test_results["delete_item_final"] = True
        else:
            print(f"Failed to soft-delete item {item_to_test_id} for final state restoration.")
            overall_pass = False

    if overall_pass:
        # 7. Confirm soft-deletion again
        print(f"\n7. Confirming item {item_to_test_id} is back in the deleted list...")
        deleted_items_url = f"{BASE_URL}/erp/stock/items/deleted" # Re-declare in case of local scope issue
        deleted_response_final = make_request("GET", deleted_items_url, headers=auth_headers)

        item_found_deleted_final = False
        if deleted_response_final and deleted_response_final.get("success"):
            data = deleted_response_final["data"]
            items = data["items"] if isinstance(data, dict) and "items" in data else data
            for item in items:
                if item.get("id") == item_to_test_id:
                    item_found_deleted_final = True
                    break
            if item_found_deleted_final:
                print(f"PASS: Item {item_to_test_id} found in deleted list after final soft-deletion.")
                test_results["verify_delete_final"] = True
            else:
                print(f"FAIL: Item {item_to_test_id} NOT found in deleted list after final soft-deletion.")
                overall_pass = False
        else:
            print("Failed to get final deleted items list.")
            overall_pass = False

    print("\n--- Test Results Summary ---")
    for step, passed in test_results.items():
        print(f"{step.replace('_', ' ').title()}: {'PASS' if passed else 'FAIL'}")

    if overall_pass:
        print("\n--- Test Finished: PASS ---")
    else:
        print("\n--- Test Finished: FAIL ---")

if __name__ == "__main__":
    main()
