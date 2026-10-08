import logging
from typing import Dict, Any, List
from app.rbac.user_context import load_user_context
from app.retrieval.hybrid_retriever import hybrid_search
from app.evaluation.rbac_oracle import expected_access

logger = logging.getLogger("app.evaluation.rbac_security_suite")

MATRIX_USERS = [
    {"role_level": "Employee", "employee_id": "STX-E-010", "name": "Meera Nair (Engineering)"},
    {"role_level": "Team Lead", "employee_id": "STX-F-005", "name": "Kunal Mehta (Finance)"},
    {"role_level": "Manager", "employee_id": "STX-HR-002", "name": "Abhishek Pandey (HR)"},
    {"role_level": "Director", "employee_id": "STX-F-001", "name": "Raghav Bansal (Finance)"},
    {"role_level": "C-Level / VP", "employee_id": "STX-L-001", "name": "Anirudh Sinha (Legal)"}
]

MATRIX_QUERIES = [
    "company working hours policy",
    "salary slip breakdown",
    "performance appraisal rating",
    "quarterly budget report",
    "executive compensation details",
    "engineering code review guidelines",
    "legal regulatory advisory budget",
    "leave history record",
    "financial audit report",
    "board meeting minutes restricted"
]

import concurrent.futures

def evaluate_matrix_combo(user_info: dict, q: str, idx: int, total: int) -> dict:
    user = load_user_context(user_info["employee_id"])
    retrieval_res = hybrid_search(q, user, limit=10)
    fused_results = retrieval_res.get("results", [])
    
    combo_violations = []
    chunks_checked = len(fused_results)

    for r in fused_results:
        payload = r["payload"]
        oracle_allowed = expected_access(user, payload)
        if not oracle_allowed:
            combo_violations.append({
                "user_id": user.employee_id,
                "user_role": user.role_level,
                "user_department": user.department,
                "query": q,
                "leaked_chunk_id": payload.get("chunk_id"),
                "document_type": payload.get("document_type"),
                "owner_employee_id": payload.get("owner_employee_id"),
                "min_clearance_level": payload.get("min_clearance_level"),
                "reason": "Oracle determined user lacks clearance or relationship for this chunk."
            })

    if idx % 10 == 0 or len(combo_violations) > 0:
        print(f"[{idx}/{total}] Matrix User: {user.employee_id} ({user.role_level}) | Query: '{q[:25]}...' | Chunks: {chunks_checked} | Leaks: {len(combo_violations)}")

    return {
        "user_id": user.employee_id,
        "role_level": user.role_level,
        "query": q,
        "chunks_retrieved": chunks_checked,
        "violations": combo_violations
    }

def run_rbac_security_suite() -> Dict[str, Any]:
    """
    Executes systematic 5x10 RBAC Security Evaluation Matrix (50 combinations) in parallel.
    Validates every retrieved chunk against the independent ground-truth RBAC oracle.
    """
    logger.info("=== STARTING PARALLEL RBAC SECURITY EVALUATION SUITE (5x10 MATRIX) ===")
    print("\n--- Starting RBAC Security Evaluation Matrix (50 Combos Parallelized) ---")
    
    total_combinations = len(MATRIX_USERS) * len(MATRIX_QUERIES)
    total_chunks_checked = 0
    violations = []
    combination_reports = []

    combo_params = []
    count = 1
    for user_info in MATRIX_USERS:
        for q in MATRIX_QUERIES:
            combo_params.append((user_info, q, count))
            count += 1

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        futures = [
            executor.submit(evaluate_matrix_combo, u, q, idx, total_combinations)
            for u, q, idx in combo_params
        ]
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            total_chunks_checked += res["chunks_retrieved"]
            if res["violations"]:
                violations.extend(res["violations"])
            combination_reports.append({
                "user_id": res["user_id"],
                "role_level": res["role_level"],
                "query": res["query"],
                "chunks_retrieved": res["chunks_retrieved"],
                "violations_in_combination": len(res["violations"])
            })

    correctly_filtered = total_chunks_checked - len(violations)
    integrity_score = (correctly_filtered / total_chunks_checked * 100.0) if total_chunks_checked > 0 else 100.0

    print(f"--- RBAC Matrix Complete: {total_chunks_checked} Chunks Checked | {len(violations)} Violations | Score: {integrity_score:.2f}% ---")
    logger.info(f"RBAC Security Suite Complete | Total Chunks: {total_chunks_checked} | Violations: {len(violations)} | Score: {integrity_score:.2f}%")

    return {
        "total_combinations_tested": total_combinations,
        "total_chunks_checked": total_chunks_checked,
        "violations_found_count": len(violations),
        "rbac_integrity_score_pct": round(integrity_score, 2),
        "violations": violations,
        "combination_summaries": combination_reports
    }
