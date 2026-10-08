from app.rbac.user_context import load_user_context
from app.retrieval.hybrid_retriever import hybrid_search
from app.evaluation.rbac_oracle import expected_access

user_hr = load_user_context('STX-HR-002')
retrieval_res = hybrid_search('salary slip breakdown', user_hr, limit=10)
for r in retrieval_res.get('results', []):
    p = r['payload']
    exp = expected_access(user_hr, p)
    print(f"Chunk: {p.get('chunk_id')} | expected_access: {exp} | access_roles: {p.get('access_roles')}")

