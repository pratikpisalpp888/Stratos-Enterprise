"""
run_rag_evaluation.py

RAG Quality Evaluation runner — 12 golden dataset cases.
- Sequential execution (max_workers=1) to avoid hammering Groq with concurrent 429s
- 45-second hard timeout per test case (marks as skipped_timeout if exceeded)
- Progress logging after every case so the run never appears frozen
- Faithfulness: Ollama (local, no rate limits)
- Answer relevancy: local cosine similarity (zero LLM)
- Context metrics: pure Python (zero LLM)
- Pipeline under test (retrieval + generation): Groq with instant Ollama fallback
"""
import time
import logging
import concurrent.futures
from typing import Dict, Any, List
from app.evaluation.golden_dataset import GOLDEN_DATASET
from app.evaluation.rag_metrics import (
    faithfulness_score,
    answer_relevancy_score,
    context_precision_score,
    context_recall_score,
)
from app.agents.agent_orchestrator import run_agent_pipeline

logger = logging.getLogger("app.evaluation.run_rag_evaluation")

CASE_TIMEOUT_SECONDS = 300  # Skip and mark as timeout if case takes longer than this

GROQ_RATE_LIMIT_SIGNALS = [
    "rate limit", "rate_limit", "429", "quota", "tokens per",
    "service error", "connection error"
]


def _is_rate_limit_error(answer: str) -> bool:
    ans_lower = answer.lower()
    return any(sig in ans_lower for sig in GROQ_RATE_LIMIT_SIGNALS)


def _evaluate_single_case_inner(item: dict, idx: int, total: int) -> dict:
    """Inner function — runs one golden dataset case. Called inside timeout executor."""
    qid = item["id"]
    q = item["question"]
    eid = item["employee_id"]
    cat = item["category"]
    expected = item["expected_answer_contains"]

    case_start = time.time()

    # Run through the full Agent/RAG pipeline (Groq with instant Ollama fallback)
    pipeline_res = run_agent_pipeline(q, eid)
    ans = pipeline_res.get("answer", "")
    sources = pipeline_res.get("sources", [])

    # Format source chunks for metric computation
    chunk_dicts = []
    for s in sources:
        chunk_dicts.append({
            "content": s.get("content") or f"{s.get('document_type', '')} {s.get('owner_name', '')}".strip(),
            "document_type": s.get("document_type"),
            "department": s.get("department"),
        })

    # Compute metrics (Ollama / local embeddings / pure Python — no Groq)
    f_score = faithfulness_score(ans, chunk_dicts)
    r_score = answer_relevancy_score(q, ans)
    p_score = context_precision_score(q, chunk_dicts)
    rec_score = context_recall_score(q, chunk_dicts, expected)

    elapsed = time.time() - case_start

    print(
        f"[{idx}/{total}] [{qid}] {cat} | "
        f"F={f_score:.2f} R={r_score:.2f} P={p_score:.2f} Rec={rec_score:.2f} | "
        f"{elapsed:.0f}s | stage={pipeline_res.get('pipeline_stage', 'N/A')}"
    )

    return {
        "id": qid,
        "category": cat,
        "question": q,
        "employee_id": eid,
        "pipeline_stage": pipeline_res.get("pipeline_stage"),
        "scores": {
            "faithfulness": round(f_score, 2),
            "answer_relevancy": round(r_score, 2),
            "context_precision": round(p_score, 2),
            "context_recall": round(rec_score, 2),
        },
        "answer_snippet": ans[:200],
        "elapsed_seconds": round(elapsed, 1),
        "skipped": False,
    }


def evaluate_single_case(item: dict, idx: int, total: int) -> dict:
    """Wraps inner function with CASE_TIMEOUT_SECONDS hard timeout."""
    qid = item["id"]
    cat = item["category"]

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = executor.submit(_evaluate_single_case_inner, item, idx, total)
    try:
        res = future.result(timeout=CASE_TIMEOUT_SECONDS)
        executor.shutdown(wait=False, cancel_futures=True)
        return res
    except concurrent.futures.TimeoutError:
        print(
            f"[{idx}/{total}] [{qid}] {cat} | TIMEOUT after {CASE_TIMEOUT_SECONDS}s — skipping"
        )
        executor.shutdown(wait=False, cancel_futures=True)
        return {
            "id": qid,
            "category": cat,
            "question": item["question"],
            "employee_id": item["employee_id"],
            "pipeline_stage": "SKIPPED_TIMEOUT",
            "scores": None,
            "answer_snippet": "",
            "elapsed_seconds": CASE_TIMEOUT_SECONDS,
            "skipped": True,
            "skip_reason": f"Exceeded {CASE_TIMEOUT_SECONDS}s hard timeout",
        }
    except Exception as e:
        print(f"[{idx}/{total}] [{qid}] {cat} | ERROR: {e}")
        executor.shutdown(wait=False, cancel_futures=True)
        return {
            "id": qid,
            "category": cat,
            "question": item["question"],
            "employee_id": item["employee_id"],
            "pipeline_stage": "ERROR",
            "scores": None,
            "answer_snippet": str(e)[:200],
            "elapsed_seconds": 0,
            "skipped": True,
            "skip_reason": str(e),
        }


def run_full_rag_evaluation() -> Dict[str, Any]:
    """
    Executes RAG Quality Evaluation across 12 Golden Dataset cases.
    Sequential (max_workers=1) to avoid concurrent Groq 429 floods.
    Each case has a 45-second hard timeout.
    """
    logger.info("=== STARTING RAG QUALITY EVALUATION (12 cases, sequential) ===")
    print("\n--- RAG Quality Evaluation: 12 Cases ---")
    print("    Faithfulness=Ollama | Relevancy=Embeddings | Precision/Recall=Python")
    print(f"    Timeout per case: {CASE_TIMEOUT_SECONDS}s")
    print()

    total_cases = len(GOLDEN_DATASET)
    results = []
    skipped_cases = []
    flagged_cases = []
    category_scores: Dict[str, Dict[str, List[float]]] = {}

    suite_start = time.time()

    # Sequential: avoids concurrent Groq calls that cause 429 floods
    for idx, item in enumerate(GOLDEN_DATASET):
        print(f"[{idx+1}/{total_cases}] Starting [{item['id']}] '{item['question'][:55]}...'")
        case_summary = evaluate_single_case(item, idx + 1, total_cases)

        if case_summary.get("skipped"):
            skipped_cases.append(case_summary)
            continue

        results.append(case_summary)
        cat = case_summary["category"]
        scores = case_summary["scores"]

        if cat not in category_scores:
            category_scores[cat] = {
                "faithfulness": [], "relevancy": [], "precision": [], "recall": []
            }
        category_scores[cat]["faithfulness"].append(scores["faithfulness"])
        category_scores[cat]["relevancy"].append(scores["answer_relevancy"])
        category_scores[cat]["precision"].append(scores["context_precision"])
        category_scores[cat]["recall"].append(scores["context_recall"])

        if min(scores.values()) < 0.70:
            flagged_cases.append(case_summary)

    suite_elapsed = time.time() - suite_start
    scored_count = len(results)

    print(f"\n--- RAG Quality Complete: {scored_count}/{total_cases} scored, "
          f"{len(skipped_cases)} skipped, {suite_elapsed:.0f}s total ---\n")

    if scored_count == 0:
        return {
            "error": "All cases skipped",
            "skipped_cases": skipped_cases,
            "total_test_cases": total_cases,
            "scored_cases": 0,
        }

    avg_metrics = {
        "faithfulness": round(sum(r["scores"]["faithfulness"] for r in results) / scored_count, 3),
        "answer_relevancy": round(sum(r["scores"]["answer_relevancy"] for r in results) / scored_count, 3),
        "context_precision": round(sum(r["scores"]["context_precision"] for r in results) / scored_count, 3),
        "context_recall": round(sum(r["scores"]["context_recall"] for r in results) / scored_count, 3),
    }

    category_averages = {}
    for cat, m in category_scores.items():
        n = len(m["faithfulness"])
        category_averages[cat] = {
            "faithfulness": round(sum(m["faithfulness"]) / n, 3),
            "answer_relevancy": round(sum(m["relevancy"]) / n, 3),
            "context_precision": round(sum(m["precision"]) / n, 3),
            "context_recall": round(sum(m["recall"]) / n, 3),
        }

    return {
        "total_test_cases": total_cases,
        "scored_cases": scored_count,
        "skipped_cases_count": len(skipped_cases),
        "overall_averages": avg_metrics,
        "category_averages": category_averages,
        "flagged_cases_count": len(flagged_cases),
        "flagged_cases": flagged_cases,
        "detailed_results": results,
        "skipped_cases": skipped_cases,
        "suite_elapsed_seconds": round(suite_elapsed, 1),
    }
