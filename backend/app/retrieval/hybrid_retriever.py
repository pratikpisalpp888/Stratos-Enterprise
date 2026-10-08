import logging
from typing import List, Dict, Any
from app.rbac.user_context import UserContext
from app.rbac.access_control import search_with_rbac
from app.retrieval.query_router import classify_query_intent
from app.retrieval.sparse_retriever import sparse_search

logger = logging.getLogger("app.retrieval.hybrid_retriever")

RRF_K = 60

def _check_rbac_permission(payload: dict, user: UserContext) -> bool:
    """
    Evaluates the 6 RBAC rules in Python for a single payload object.
    Used to ensure sparse (BM25) candidates strictly respect security policy.
    """
    sens = payload.get("sensitivity_level", "Internal")
    dept = payload.get("department")
    min_clr = payload.get("min_clearance_level", 1)
    is_personal = payload.get("restricted_to_owner", False)
    owner_id = payload.get("owner_employee_id")
    mgr_id = payload.get("manager_id")
    access_roles = payload.get("access_roles") or []

    # Rule 1: Public
    if sens == "Public":
        return True

    # Rule 2: Dept + Clearance (company-wide)
    if dept and dept == user.department and min_clr <= user.clearance_level and not is_personal:
        return True

    # Rule 3: Cross-Dept Executive (Clearance >= 3, company-wide)
    if user.clearance_level >= 3 and min_clr <= user.clearance_level and not is_personal:
        return True

    # Rule 4: Self-Ownership
    if owner_id and owner_id == user.employee_id:
        return True

    # Rule 5: Manager Access
    if mgr_id and mgr_id == user.employee_id:
        return True

    # Rule 6a: HR-Admin Privilege
    if user.is_hr_admin and "HR-Admin" in access_roles:
        return True

    # Rule 6b: Finance-Admin Privilege
    if user.is_finance_admin and "Finance-Admin" in access_roles:
        return True

    return False


def hybrid_search(
    query: str,
    user: UserContext,
    limit: int = 5
) -> Dict[str, Any]:
    """
    Executes hybrid retrieval (Dense + Sparse) with RBAC filtering, RRF fusion,
    and intent-based reranking.
    """
    # 1. Query Intent Classification
    intent_data = classify_query_intent(query)
    intent = intent_data["intent"]
    confidence = intent_data["confidence"]

    # For aggregate/summary queries, expand candidate pool to limit=10 for broader coverage
    search_limit = 10 if intent == "aggregate_or_report" else limit

    # 2. Dense Search (RBAC-Filtered in Qdrant)
    dense_candidates = search_with_rbac(query, user, limit=20)

    # 3. Sparse Search (BM25)
    sparse_raw = sparse_search(query, limit=20)

    # 4. Filter Sparse Candidates against RBAC in Python
    sparse_candidates = []
    for cand in sparse_raw:
        payload = cand["payload"]
        if _check_rbac_permission(payload, user):
            sparse_candidates.append(cand)
        else:
            logger.debug(f"BM25 candidate {cand['chunk_id']} rejected by RBAC for user {user.employee_id}")

    # Map chunk_ids to candidates and track ranks
    candidate_map: Dict[str, Dict] = {}

    # Track dense ranks
    for rank, cand in enumerate(dense_candidates, start=1):
        cid = cand["chunk_id"]
        candidate_map[cid] = {
            "chunk_id": cid,
            "dense_rank": rank,
            "sparse_rank": None,
            "dense_score": cand["score"],
            "bm25_score": None,
            "payload": {
                "chunk_id": cand["chunk_id"],
                "content": cand.get("content", ""),
                "document_type": cand.get("document_type"),
                "department": cand.get("department"),
                "sensitivity_level": cand.get("sensitivity_level"),
                "owner_employee_id": cand.get("owner_employee_id"),
                "owner_name": cand.get("owner_name"),
                "restricted_to_owner": cand.get("restricted_to_owner"),
                "min_clearance_level": cand.get("min_clearance_level"),
                "manager_id": cand.get("manager_id"),
                "access_roles": cand.get("access_roles"),
                "source_file": cand.get("source_file"),
            }
        }

    # Track sparse ranks
    for rank, cand in enumerate(sparse_candidates, start=1):
        cid = cand["chunk_id"]
        if cid in candidate_map:
            candidate_map[cid]["sparse_rank"] = rank
            candidate_map[cid]["bm25_score"] = cand["bm25_score"]
        else:
            candidate_map[cid] = {
                "chunk_id": cid,
                "dense_rank": None,
                "sparse_rank": rank,
                "dense_score": None,
                "bm25_score": cand["bm25_score"],
                "payload": cand["payload"]
            }

    # 5. RRF Fusion + 6. Intent Boosting
    fused_results = []
    for cid, item in candidate_map.items():
        payload = item["payload"]
        rrf_score = 0.0
        
        if item["dense_rank"] is not None:
            rrf_score += 1.0 / (RRF_K + item["dense_rank"])
        if item["sparse_rank"] is not None:
            rrf_score += 1.0 / (RRF_K + item["sparse_rank"])

        # Intent Boosting Logic
        multiplier = 1.0
        is_personal = payload.get("restricted_to_owner", False) or payload.get("owner_employee_id") is not None
        doc_type = payload.get("document_type") or ""

        if intent == "personal_record_lookup":
            if is_personal:
                multiplier = 2.5
        elif intent == "policy_or_general_info":
            if not is_personal and ("Policy" in doc_type or "Handbook" in doc_type or "Guidelines" in doc_type or "Overview" in doc_type or "FAQ" in doc_type):
                multiplier = 2.5
        elif intent == "aggregate_or_report":
            if not is_personal and ("Report" in doc_type or "Budget" in doc_type or "Audit" in doc_type or "Summary" in doc_type):
                multiplier = 2.5

        final_score = rrf_score * multiplier

        item["rrf_score"] = round(rrf_score, 6)
        item["intent_multiplier"] = multiplier
        item["final_score"] = round(final_score, 6)
        fused_results.append(item)

    # 7. Sort by final_score descending
    fused_results.sort(key=lambda x: x["final_score"], reverse=True)

    top_results = fused_results[:search_limit]

    logger.info(f"Hybrid retrieval for '{query[:30]}' (intent={intent}) returned {len(top_results)} results.")
    
    return {
        "intent_classification": {
            "intent": intent,
            "confidence": confidence
        },
        "total_candidates": len(candidate_map),
        "results": top_results
    }
