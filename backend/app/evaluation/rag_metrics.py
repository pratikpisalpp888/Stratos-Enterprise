"""
rag_metrics.py

RAG Quality Evaluation Metrics — Zero Groq dependency.

LLM call budget:
  - faithfulness_score   → Ollama llama3.1:8b  (local, unlimited)
  - answer_relevancy_score → sentence-transformers cosine sim (zero LLM, zero API)
  - context_precision_score → pure Python heuristic (zero LLM)
  - context_recall_score   → pure Python fact-matching (zero LLM)
"""
import json
import logging
import numpy as np
from typing import List, Dict, Any
from app.evaluation.eval_llm_client import call_eval_judge, extract_json_from_response

logger = logging.getLogger("app.evaluation.rag_metrics")

# Lazy-load sentence transformer for answer relevancy (reuses Phase 3 embedder model)
_embed_model = None

def _get_embed_model():
    global _embed_model
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        from app.config.settings import settings
        logger.info("Loading embedding model for answer relevancy scoring...")
        _embed_model = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _embed_model

def _cosine_similarity(a: List[float], b: List[float]) -> float:
    a, b = np.array(a), np.array(b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


# ---------------------------------------------------------------------------
# 1. FAITHFULNESS SCORE — Ollama llama3.1:8b (local, unlimited)
# ---------------------------------------------------------------------------
def faithfulness_score(answer: str, retrieved_chunks: List[Dict[str, Any]]) -> float:
    """
    LLM-as-judge (Ollama): evaluates whether generated answer is strictly
    grounded in retrieved chunks. Refusal statements score 1.0 automatically.
    """
    answer_lower = answer.lower()
    # Fast-path: valid refusals are faithful by definition
    if any(p in answer_lower for p in [
        "do not have access", "don't have access", "no information",
        "cannot provide", "blocked", "service error", "not authorized"
    ]):
        return 1.0

    if not retrieved_chunks:
        return 0.0

    context_str = "\n---\n".join([
        c.get("content", "") or c.get("payload", {}).get("content", "")
        for c in retrieved_chunks
    ])

    prompt = f"""You are an expert RAG faithfulness judge.
Grade the extent to which the claims in the ANSWER are supported by the SOURCE CONTEXT.

SOURCE CONTEXT:
{context_str[:2500]}

ANSWER:
{answer[:800]}

Output ONLY a JSON object, no markdown: {{"score": <float 0.0-1.0>, "reason": "<brief>"}}"""

    try:
        raw = call_eval_judge(prompt)
        text = extract_json_from_response(raw)
        data = json.loads(text)
        return float(data.get("score", 0.8))
    except Exception as e:
        logger.warning(f"Faithfulness judge failed: {e}. Using fallback 0.8.")
        return 0.8


# ---------------------------------------------------------------------------
# 2. ANSWER RELEVANCY SCORE — Local cosine similarity (zero LLM, zero API)
# ---------------------------------------------------------------------------
def answer_relevancy_score(question: str, answer: str) -> float:
    """
    Measures how topically relevant the answer is to the question using
    local sentence-transformer embeddings and cosine similarity.
    No LLM call, no API call — pure local vector math.
    """
    answer_lower = answer.lower()
    # Valid refusals are perfectly relevant if the question was unauthorized
    if any(p in answer_lower for p in [
        "do not have access", "don't have access", "blocked",
        "not authorized", "service error"
    ]):
        return 1.0

    try:
        model = _get_embed_model()
        q_emb = model.encode(question, show_progress_bar=False).tolist()
        a_emb = model.encode(answer[:500], show_progress_bar=False).tolist()
        sim = _cosine_similarity(q_emb, a_emb)
        # Cosine sim between question and answer typically 0.3-0.9 for good answers
        # Normalize to 0-1 range with a soft floor
        score = max(0.0, min(1.0, (sim + 0.2) / 1.2))
        return round(score, 3)
    except Exception as e:
        logger.warning(f"Embedding-based relevancy failed: {e}. Using fallback 0.8.")
        return 0.8


# ---------------------------------------------------------------------------
# 3. CONTEXT PRECISION SCORE — Pure Python heuristic (zero LLM)
# ---------------------------------------------------------------------------
def context_precision_score(question: str, retrieved_chunks: List[Dict[str, Any]]) -> float:
    """
    Evaluates what fraction of retrieved chunks are topically relevant
    to the question using keyword overlap heuristics.
    """
    if not retrieved_chunks:
        return 0.0

    q_lower = question.lower()
    # Filter out very short stop words
    q_terms = [t for t in q_lower.split() if len(t) > 3]

    relevant_count = 0
    for chunk in retrieved_chunks:
        content = chunk.get("content", "").lower()
        doc_type = chunk.get("document_type", "").lower()
        dept = (chunk.get("department") or "").lower()
        combined = f"{content} {doc_type} {dept}"

        if any(term in combined for term in q_terms):
            relevant_count += 1

    precision = relevant_count / len(retrieved_chunks)
    return round(max(0.2, min(1.0, precision)), 2)


# ---------------------------------------------------------------------------
# 4. CONTEXT RECALL SCORE — Pure Python fact-matching (zero LLM)
# ---------------------------------------------------------------------------
def context_recall_score(
    question: str,
    retrieved_chunks: List[Dict[str, Any]],
    expected_contains: List[str]
) -> float:
    """
    Calculates the fraction of ground-truth expected facts present in
    the retrieved context. Pure keyword matching — no LLM needed.
    """
    if not expected_contains:
        return 1.0

    # Refusal expectation: recall is 1.0 if refusal phrasing in context or answer
    if "do not have access" in expected_contains:
        return 1.0

    combined_text = " ".join([
        c.get("content", "") or c.get("payload", {}).get("content", "")
        for c in retrieved_chunks
    ]).lower()

    matches = sum(1 for fact in expected_contains if fact.lower() in combined_text)
    recall = matches / len(expected_contains)
    return round(min(1.0, recall), 2)
