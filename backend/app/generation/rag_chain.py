import time
import logging
from typing import Dict, Any
from app.rbac.user_context import load_user_context
from app.guardrails.input_guardrails import run_input_guardrails
from app.guardrails.output_guardrails import run_output_guardrails
from app.retrieval.hybrid_retriever import hybrid_search
from app.generation.llm_generator import generate_answer

logger = logging.getLogger("app.generation.rag_chain")

def run_rag_pipeline(query: str, employee_id: str) -> Dict[str, Any]:
    """
    Executes the complete SentinelRAG end-to-end pipeline:
    Query -> UserContext -> Input Guardrails -> Hybrid Retrieval -> LLM Generation -> Output Guardrails -> Final Response.
    """
    start_time = time.time()
    logger.info(f"--- START RAG PIPELINE | User: {employee_id} | Query: '{query[:50]}' ---")

    # 1. Resolve User Context
    try:
        user = load_user_context(employee_id)
        logger.info(f"Resolved user context: {user.full_name} ({user.role_level}/{user.department})")
    except ValueError as e:
        logger.error(f"User context resolution failed for {employee_id}: {e}")
        return {
            "answer": f"Error: User '{employee_id}' not found in employee roster.",
            "pipeline_stage": "USER_RESOLUTION_FAILED",
            "sources": [],
            "intent_classification": None,
            "guardrail_flags": ["INVALID_EMPLOYEE_ID"],
            "response_time_ms": round((time.time() - start_time) * 1000, 2)
        }

    # 2. Run Input Guardrails
    input_g = run_input_guardrails(query)
    if not input_g["passed"]:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.warning(f"Pipeline stopped at INPUT_GUARDRAILS: {input_g['block_reason']}")
        return {
            "answer": input_g["block_reason"],
            "pipeline_stage": "INPUT_GUARDRAIL_BLOCK",
            "sources": [],
            "intent_classification": None,
            "guardrail_flags": ["INPUT_GUARDRAIL_BLOCKED"],
            "response_time_ms": round(elapsed_ms, 2)
        }

    # 3. Execute Hybrid Search (RBAC + BM25 + Intent Reranking)
    retrieval_res = hybrid_search(query, user, limit=5)
    fused_results = retrieval_res["results"]
    retrieved_chunks = [r["payload"] for r in fused_results]

    # Format sources for response metadata
    sources = []
    for r in fused_results:
        p = r["payload"]
        sources.append({
            "chunk_id": p.get("chunk_id"),
            "content": p.get("content"),
            "document_type": p.get("document_type"),
            "department": p.get("department"),
            "owner_name": p.get("owner_name"),
            "final_score": r.get("final_score")
        })

    # 4. Handle Zero Retrieval Candidates
    if not retrieved_chunks:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.info(f"Zero chunks retrieved for query '{query[:30]}'. Returning graceful no-data response.")
        return {
            "answer": "I don't have information about this in our knowledge base. Please contact the relevant department for assistance.",
            "pipeline_stage": "ZERO_RETRIEVAL_NO_DATA",
            "sources": [],
            "intent_classification": retrieval_res["intent_classification"],
            "guardrail_flags": [],
            "response_time_ms": round(elapsed_ms, 2)
        }

    # 5. LLM Generation
    raw_answer = generate_answer(query, retrieved_chunks, user)

    # 6. Run Output Guardrails
    output_g = run_output_guardrails(raw_answer, retrieved_chunks, user)
    
    elapsed_ms = (time.time() - start_time) * 1000
    pipeline_stage = "SUCCESSFUL_GENERATION" if output_g["passed"] else "OUTPUT_GUARDRAIL_BLOCK"
    
    logger.info(f"--- COMPLETED RAG PIPELINE | Stage: {pipeline_stage} | Time: {elapsed_ms:.2f}ms ---")

    return {
        "answer": output_g["final_answer"],
        "pipeline_stage": pipeline_stage,
        "sources": sources,
        "intent_classification": retrieval_res["intent_classification"],
        "guardrail_flags": output_g["flags"],
        "response_time_ms": round(elapsed_ms, 2)
    }
