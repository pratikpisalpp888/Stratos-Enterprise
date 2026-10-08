import uuid
from app.rbac.user_context import load_user_context
from app.retrieval.hybrid_retriever import hybrid_search
from app.evaluation.rbac_oracle import expected_access

user_hr = load_user_context("STX-HR-002")

queries = ["salary slip breakdown", "executive compensation details", "board meeting minutes restricted"]

print("=== INSPECTING THE 13 FLAGGED SALARY SLIP CHUNKS ===")
for q in queries:
    res = hybrid_search(q, user_hr, limit=10)
    for r in res["results"]:
        p = r["payload"]
        if not expected_access(user_hr, p):
            print(f"Query: '{q}' | Chunk ID: {p.get('chunk_id')} | Type: {p.get('document_type')} | Owner: {p.get('owner_name')} ({p.get('owner_employee_id')}) | access_roles: {p.get('access_roles')}")

