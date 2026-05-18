import urllib.request
base_url = "http://localhost:8000/api/v1"
request = urllib.request.Request(f"{base_url}/dev/sync", method="POST")
try:
    with urllib.request.urlopen(request) as response:
        print("SYNC:", response.status)
except urllib.error.HTTPError as e:
    print("SYNC ERROR:", e.code, e.read().decode())
