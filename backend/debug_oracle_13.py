from app.rbac.user_context import load_user_context
from app.evaluation.rbac_security_suite import run_rbac_security_suite
from app.evaluation.rbac_oracle import expected_access

res = run_rbac_security_suite()
print(f"Total Violations: {len(res['violations'])}")
for idx, v in enumerate(res['violations']):
    user = load_user_context(v['user_id'])
    # Re-evaluate chunk directly
    from app.retrieval.qdrant_client import get_client
    import uuid
    client = get_client()
    pt_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, v['leaked_chunk_id']))
    points = client.retrieve(collection_name='stratos_documents', ids=[pt_id])
    if points:
        payload = points[0].payload
        oracle_res = expected_access(user, payload)
        print(f"[{idx+1}] Chunk: {v['leaked_chunk_id']} | User: {user.employee_id} ({user.role_level}) | is_hr_admin: {user.is_hr_admin} | access_roles: {payload.get('access_roles')} | oracle_res: {oracle_res}")

