import subprocess
import urllib.request
import json
import time

print("Starting Uvicorn server...")
process = subprocess.Popen(
    ["uvicorn", "app.main:app", "--port", "8000"],
    cwd=r"d:\2026\Stratos Enterprise\backend"
)

# Wait for server to start
time.sleep(12)

try:
    print("\n--- Testing /qdrant-check ---")
    req = urllib.request.urlopen("http://localhost:8000/qdrant-check")
    res = json.loads(req.read().decode('utf-8'))
    print("Qdrant Check Response:", json.dumps(res, indent=2))
    
    print("\n--- Testing /ingest/vectorize (This will download model & embed 1,927 chunks) ---")
    post_req = urllib.request.Request("http://localhost:8000/ingest/vectorize", method="POST")
    req2 = urllib.request.urlopen(post_req, timeout=300) # Give it 5 mins
    res2 = json.loads(req2.read().decode('utf-8'))
    print("Vectorize Response:", json.dumps(res2, indent=2))
    
    queries = [
        "employee handbook policies",
        "salary breakdown and deductions",
        "leave balance and history"
    ]
    
    for q in queries:
        print(f"\n--- Testing /vector-search-test?query={q.replace(' ', '+')} ---")
        url = f"http://localhost:8000/vector-search-test?query={urllib.parse.quote(q)}&limit=1"
        req_search = urllib.request.urlopen(url)
        res_search = json.loads(req_search.read().decode('utf-8'))
        print(f"Search Results for '{q}':", json.dumps(res_search, indent=2))

except Exception as e:
    print("Error encountered:", e)
finally:
    print("Stopping Uvicorn server...")
    process.terminate()
    try:
        process.wait(timeout=5)
    except:
        process.kill()
