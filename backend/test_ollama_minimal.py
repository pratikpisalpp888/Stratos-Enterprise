"""
Minimal timed Ollama test - verifies single call completes within timeout.
"""
import sys
import time
import signal

sys.path.insert(0, ".")

TIMEOUT_SECONDS = 30

def run_test():
    print(f"Starting minimal Ollama test (timeout: {TIMEOUT_SECONDS}s)...")
    start = time.time()
    
    try:
        from ollama import Client
        client = Client(host="http://localhost:11434")
        
        # Test 1: ping the model list first
        print("Step 1: Listing available models...")
        models = client.list()
        print(f"  Models available: {[m['name'] for m in models.get('models', [])]}")
        
        # Test 2: single inference with short output
        print("Step 2: Single inference call (simple, short response)...")
        response = client.chat(
            model="llama3.2:1b",  # smaller/faster model first
            messages=[{"role": "user", "content": "Reply with only this JSON: {\"ok\": true}"}],
            format="json",
            options={"temperature": 0.0, "num_predict": 20}
        )
        elapsed = time.time() - start
        text = response["message"]["content"]
        print(f"  Response in {elapsed:.1f}s: {text}")
        print("SUCCESS - llama3.2:1b is fast and responsive!")
        return "1b", elapsed
        
    except Exception as e:
        elapsed = time.time() - start
        print(f"  llama3.2:1b failed after {elapsed:.1f}s: {e}")
        
        # Try 8b as fallback
        try:
            print("Step 3: Trying llama3.1:8b...")
            start2 = time.time()
            from ollama import Client
            client = Client(host="http://localhost:11434")
            response = client.chat(
                model="llama3.1:8b",
                messages=[{"role": "user", "content": "Reply with only this JSON: {\"ok\": true}"}],
                format="json",
                options={"temperature": 0.0, "num_predict": 20}
            )
            elapsed2 = time.time() - start2
            text = response["message"]["content"]
            print(f"  Response in {elapsed2:.1f}s: {text}")
            print("INFO - llama3.1:8b works but may be slow for batch evaluation")
            return "8b", elapsed2
        except Exception as e2:
            print(f"  llama3.1:8b failed: {e2}")
            return None, 0

model, elapsed = run_test()
print(f"\nDiagnosis result: model={model}, time={elapsed:.1f}s")
if elapsed > 30:
    print("RECOMMENDATION: Use llama3.2:1b for evaluation - much faster on this 16GB system")
elif model is None:
    print("RECOMMENDATION: Ollama is not responding - check server status")
else:
    print(f"RECOMMENDATION: Use {model} - acceptable response time")
