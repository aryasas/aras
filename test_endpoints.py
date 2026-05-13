import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

# Login to get token
response = client.post("/api/v1/auth/login", data={"username": "admin", "password": "password"})
# wait what is the password?
print(response.json())

# Just hit endpoints
r1 = client.post("/api/v1/dev/sync")
print("SYNC RESPONSE:", r1.status_code, r1.json())

r2 = client.post("/api/v1/query/sys_settings", json={"filters": []})
print("QUERY RESPONSE:", r2.status_code, r2.json())

