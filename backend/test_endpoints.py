import subprocess
import urllib.request
import json
import time
import sys
import os

# Set environment variable to suppress warnings
env = os.environ.copy()

process = subprocess.Popen(
    ["uvicorn", "app.main:app", "--port", "8000"],
    cwd=r"d:\2026\Stratos Enterprise\backend",
    env=env
)

time.sleep(5)

try:
    health_req = urllib.request.urlopen("http://localhost:8000/health")
    health_res = json.loads(health_req.read().decode('utf-8'))
    print("Health check response:", json.dumps(health_res, indent=2))

    data_req = urllib.request.urlopen("http://localhost:8000/data-check")
    data_res = json.loads(data_req.read().decode('utf-8'))
    print("\nData check response:", json.dumps(data_res, indent=2))
except Exception as e:
    print(f"Error: {e}")
finally:
    process.terminate()
    try:
        process.wait(timeout=5)
    except:
        process.kill()
