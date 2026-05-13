import urllib.request
request = urllib.request.Request("http://localhost:8000/api/v1/dev/sync", method="OPTIONS")
request.add_header("Origin", "http://localhost:5173")
request.add_header("Access-Control-Request-Method", "POST")
request.add_header("Access-Control-Request-Headers", "Authorization")

try:
    with urllib.request.urlopen(request) as response:
        print("OPTIONS STATUS:", response.status)
        print("OPTIONS HEADERS:", response.headers)
except urllib.error.HTTPError as e:
    print("OPTIONS ERROR:", e.code, e.headers)
