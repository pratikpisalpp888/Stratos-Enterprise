"""
eval_llm_client.py

Central client for ALL evaluation judge/scoring LLM calls.
Uses local Ollama (llama3.1:8b) - 100% free, unlimited, no rate limits.

IMPORTANT: The production chatbot pipeline (RAG generation, query routing,
guardrails) stays on Groq. ONLY the evaluation metric judges use this module.
"""
import re
import time
import logging
from ollama import Client
from app.config.settings import settings

logger = logging.getLogger("app.evaluation.eval_llm_client")

_ollama_client = None

def _get_client() -> Client:
    global _ollama_client
    if _ollama_client is None:
        # timeout=60 ensures no call hangs indefinitely — fails cleanly after 60s
        _ollama_client = Client(host=settings.OLLAMA_BASE_URL, timeout=60)
    return _ollama_client

def call_eval_judge(prompt: str, max_retries: int = 3) -> str:
    """
    Calls the local Ollama LLM (llama3.1:8b) for evaluation judge tasks.
    Uses format='json' to enforce constrained JSON output at the model level.
    Hard timeout: 60 seconds per call. Raises RuntimeError if all retries fail.

    This function is the ONLY LLM call used by rag_metrics.py and red_team_suite.py.
    Production pipeline calls are NOT routed through here.
    """
    client = _get_client()
    for attempt in range(1, max_retries + 1):
        try:
            response = client.chat(
                model=settings.OLLAMA_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a JSON-only responder. You MUST output ONLY valid JSON. No prose, no explanation, no markdown."
                    },
                    {"role": "user", "content": prompt}
                ],
                format="json",  # Ollama constrained decoding — forces valid JSON output
                options={"temperature": 0.0, "num_predict": 200}
            )
            text = response["message"]["content"].strip()
            logger.debug(f"Ollama eval judge response (attempt {attempt}): {text[:80]}")
            return text
        except Exception as e:
            logger.warning(f"Ollama eval judge attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                time.sleep(2)
    raise RuntimeError(f"Ollama eval judge failed after {max_retries} attempts.")


def extract_json_from_response(text: str) -> str:
    """
    Robust JSON extractor: strips markdown code fences and Ollama think-blocks,
    then extracts the first valid JSON object or array.
    """
    # Strip <think>...</think> blocks (Qwen/DeepSeek style)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()
    # Strip markdown code fences
    text = re.sub(r"```(?:json)?", "", text).strip().rstrip("```").strip()
    # Extract first JSON object or array
    match = re.search(r"(\{.*?\}|\[.*?\])", text, re.DOTALL)
    if match:
        return match.group(1)
    return text.strip()
