from app.evaluation.rbac_security_suite import run_rbac_security_suite

res = run_rbac_security_suite()
print(f"Total Chunks: {res['total_chunks_checked']} | Violations: {res['violations_found_count']}")
for idx, v in enumerate(res['violations']):
    print(f"[{idx+1}] User: {v['user_id']} ({v['user_role']}) | Query: '{v['query']}' | Chunk: {v['leaked_chunk_id']} | Type: {v['document_type']}")

