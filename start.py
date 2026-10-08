import os
import sys

print("===================================================", flush=True)
print("[STARTUP] BOOTING STRATOS SENTINELRAG BACKEND SERVER...", flush=True)
print(f"[STARTUP] Python: {sys.version}", flush=True)
print(f"[STARTUP] CWD: {os.getcwd()}", flush=True)

# Add current directory and backend to path
sys.path.insert(0, os.getcwd())
if os.path.exists(os.path.join(os.getcwd(), "backend")):
    sys.path.insert(0, os.path.join(os.getcwd(), "backend"))

port = int(os.environ.get("PORT", 10000))
print(f"[STARTUP] Target Port: {port}", flush=True)
print(f"[STARTUP] Checking environment variables:", flush=True)
print(f"  GROQ_API_KEY set: {'GROQ_API_KEY' in os.environ and bool(os.environ['GROQ_API_KEY'])}", flush=True)
print(f"  QDRANT_URL: {os.environ.get('QDRANT_URL', 'NOT SET')}", flush=True)

try:
    import uvicorn
    from app.main import app
    print(f"[STARTUP] FastAPI app imported successfully! Starting Uvicorn on 0.0.0.0:{port}...", flush=True)
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
except Exception as e:
    import traceback
    print("[STARTUP ERROR] FATAL ERROR DURING STARTUP:", flush=True)
    traceback.print_exc()
    sys.exit(1)
