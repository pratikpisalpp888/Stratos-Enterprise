"""
Minimal single call_eval_judge test - confirms it responds within 30s.
"""
import sys
import time
sys.path.insert(0, ".")

from app.evaluation.eval_llm_client import call_eval_judge, extract_json_from_response
import json

print("=" * 60)
print("MINIMAL SINGLE call_eval_judge() TEST")
print("=" * 60)

prompt = """Grade the faithfulness of this answer.
SOURCE CONTEXT: The standard working hours at Stratos Enterprises are 9:00 AM to 6:00 PM, Monday through Friday.
ANSWER: Employees work from 9 AM to 6 PM, Monday to Friday.
Output ONLY JSON: {"score": <float>, "reason": "<brief>"}"""

print(f"Sending prompt to Ollama llama3.1:8b (30s hard timeout)...")
start = time.time()
try:
    raw = call_eval_judge(prompt)
    elapsed = time.time() - start
    print(f"Response received in {elapsed:.1f}s:")
    print(f"  Raw: {raw[:200]}")
    
    extracted = extract_json_from_response(raw)
    data = json.loads(extracted)
    print(f"  Score: {data.get('score')}")
    print(f"  Reason: {data.get('reason')}")
    print(f"\nRESULT: SUCCESS in {elapsed:.1f}s - ready for full evaluation suite")
except Exception as e:
    elapsed = time.time() - start
    print(f"RESULT: FAILED after {elapsed:.1f}s - {e}")
    sys.exit(1)
