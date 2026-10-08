import subprocess
import urllib.request
import json
import time
import os

env = os.environ.copy()
env['GROQ_API_KEY'] = 'dummy_key'

process = subprocess.Popen(
    ["uvicorn", "app.main:app", "--port", "8000"],
    cwd=r"d:\2026\Stratos Enterprise\backend",
    env=env
)

time.sleep(5)

try:
    print("Testing /llm-check...")
    llm_req = urllib.request.urlopen("http://localhost:8000/llm-check")
    llm_res = json.loads(llm_req.read().decode('utf-8'))
    print("LLM Check Response:", json.dumps(llm_res, indent=2))
except Exception as e:
    print(f"Error testing LLM check: {e}")

try:
    print("\nTesting /ingest/run...")
    req = urllib.request.Request("http://localhost:8000/ingest/run", method="POST")
    ingest_req = urllib.request.urlopen(req)
    ingest_res = json.loads(ingest_req.read().decode('utf-8'))
    print("Ingest Run Response:", json.dumps(ingest_res, indent=2))
except Exception as e:
    print(f"Error testing Ingest run: {e}")
finally:
    process.terminate()
    try:
        process.wait(timeout=5)
    except:
        process.kill()
