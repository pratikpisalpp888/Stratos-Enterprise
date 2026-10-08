import sys
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("\n================================================================================")
print("PHASE 10: END-TO-END BACKEND API LAYER & AUTHENTICATION VERIFICATION")
print("================================================================================\n")

# Step 1: POST /api/v1/auth/login with employee_id "STX-E-010" (Meera Nair)
print("[STEP 1/5] Testing Login for STX-E-010 (Meera Nair - Employee level)...")
res1 = client.post("/api/v1/auth/login", json={"employee_id": "STX-E-010"})
assert res1.status_code == 200, f"Login failed: {res1.text}"
data1 = res1.json()
meera_token = data1["access_token"]
user_info1 = data1["user"]

print(f"  -> SUCCESS! Status Code: {res1.status_code}")
print(f"  -> User: {user_info1['full_name']} ({user_info1['role_level']} / {user_info1['department']})")
print(f"  -> Token (prefix): {meera_token[:25]}...\n")

# Step 2: POST /api/v1/chat/query using Bearer token (no employee_id in body)
print("[STEP 2/5] Testing Chat Pipeline using Auth Token (query: 'What is my salary breakdown?')...")
headers1 = {"Authorization": f"Bearer {meera_token}"}
res2 = client.post(
    "/api/v1/chat/query",
    headers=headers1,
    json={"query": "What is my salary breakdown?"}
)
assert res2.status_code == 200, f"Chat query failed: {res2.text}"
data2 = res2.json()

print(f"  -> SUCCESS! Status Code: {res2.status_code}")
print(f"  -> Intent: {data2['intent']}")
print(f"  -> Sources Count: {len(data2['sources'])}")
print(f"  -> Answer Snippet: '{data2['answer'][:120]}...'\n")

# Step 3: GET /api/v1/admin/audit-logs with Employee token -> Expected 403 Forbidden
print("[STEP 3/5] Testing Admin Endpoint Access with Employee Token (Meera Nair)...")
res3 = client.get("/api/v1/admin/audit-logs", headers=headers1)
assert res3.status_code == 403, f"Expected 403 Forbidden, got {res3.status_code}: {res3.text}"
data3 = res3.json()

print(f"  -> SUCCESS! Correctly Blocked with 403 Forbidden.")
print(f"  -> Error Response: {data3['error']} - {data3['detail']}\n")

# Step 4: Login as HR Manager (STX-HR-002) and call admin audit logs -> Expected 200 OK
print("[STEP 4/5] Testing Login as HR Manager (STX-HR-002) & Accessing Admin Audit Logs...")
res4_login = client.post("/api/v1/auth/login", json={"employee_id": "STX-HR-002"})
assert res4_login.status_code == 200, f"HR Manager login failed: {res4_login.text}"
hr_token = res4_login.json()["access_token"]
hr_headers = {"Authorization": f"Bearer {hr_token}"}

res4_admin = client.get("/api/v1/admin/audit-logs", headers=hr_headers)
assert res4_admin.status_code == 200, f"Admin audit logs failed for HR Manager: {res4_admin.text}"
logs = res4_admin.json()

print(f"  -> SUCCESS! Status Code: {res4_admin.status_code}")
print(f"  -> Audit Logs Count Retrieved: {len(logs)}\n")

# Step 5: Call protected endpoint (/api/v1/user/me) with NO token or INVALID token -> Expected 401 Unauthorized
print("[STEP 5/5] Testing Protected Endpoint Access with Invalid/Missing Token...")
res5_no_token = client.get("/api/v1/user/me")
assert res5_no_token.status_code in [401, 403], f"Expected 401/403 for missing token, got {res5_no_token.status_code}"

res5_invalid = client.get("/api/v1/user/me", headers={"Authorization": "Bearer invalid_token_12345"})
assert res5_invalid.status_code == 401, f"Expected 401 Unauthorized for invalid token, got {res5_invalid.status_code}"
data5 = res5_invalid.json()

print(f"  -> SUCCESS! Correctly Blocked with 401 Unauthorized.")
print(f"  -> Error Response: {data5['error']} - {data5['detail']}\n")

print("================================================================================")
print("ALL 5 PHASE 10 API LAYER & AUTHENTICATION TESTS PASSED PERFECTLY!")
print("================================================================================")
