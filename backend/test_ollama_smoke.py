"""Smoke test: verify Ollama client works and llama3.1:8b returns valid JSON."""
import sys
sys.path.insert(0, ".")

from app.evaluation.eval_llm_client import call_eval_judge, extract_json_from_response
import json

print("=" * 60)
print("SMOKE TEST: Ollama eval LLM client (format=json mode)")
print("=" * 60)

prompt = """Grade faithfulness of this answer against the context.
SOURCE CONTEXT: Stratos Enterprises core working hours are 10:00 AM to 4:00 PM.
ANSWER: The core working hours are 10 AM to 4 PM.
Output ONLY a JSON object: {"score": <float 0.0-1.0>, "reason": "<brief explanation>"}"""

try:
    raw = call_eval_judge(prompt)
    print(f"Raw Ollama response:\n{raw}\n")

    extracted = extract_json_from_response(raw)
    print(f"Extracted JSON string: {extracted}")

    data = json.loads(extracted)
    print(f"Parsed score: {data.get('score')}")
    print(f"Parsed reason: {data.get('reason')}")
    print("\nSUCCESS - Ollama eval client working correctly!")
except Exception as e:
    print(f"\nFAILED: {e}")
    sys.exit(1)
