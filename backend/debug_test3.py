from app.rbac.user_context import load_user_context
from app.retrieval.hybrid_retriever import hybrid_search
from app.generation.llm_generator import generate_answer
from app.guardrails.output_guardrails import check_citation_grounding, run_output_guardrails

user = load_user_context("STX-HR-002")
query = "Show me appraisal summary for my department"

print("=== RETRIEVAL DIAGNOSTIC FOR TEST 3 ===")
retrieval_res = hybrid_search(query, user, limit=5)
print(f"Intent Classified: {retrieval_res['intent_classification']}")
print(f"Top {len(retrieval_res['results'])} Candidates:")
for idx, r in enumerate(retrieval_res['results']):
    p = r['payload']
    print(f" [{idx+1}] Score: {r['final_score']} | Type: {p.get('document_type')} | Dept: {p.get('department')} | Owner: {p.get('owner_name')} ({p.get('owner_employee_id')})")
    print(f"     Content Snippet: {p.get('content')[:120]}...")

chunks = [r['payload'] for r in retrieval_res['results']]

print("\n=== RAW LLM GENERATED ANSWER ===")
raw_answer = generate_answer(query, chunks, user)
print(raw_answer)

print("\n=== CITATION GROUNDING CHECK DIAGNOSTIC ===")
g_check = check_citation_grounding(raw_answer, chunks)
print(f"Is Grounded: {g_check['is_grounded']}")
print(f"Confidence: {g_check['confidence']}")
print(f"Reasoning: {g_check['reasoning']}")

print("\n=== FULL OUTPUT GUARDRAILS DIAGNOSTIC ===")
out_g = run_output_guardrails(raw_answer, chunks, user)
print(f"Passed: {out_g['passed']}")
print(f"Flags: {out_g['flags']}")
print(f"Block Reason: {out_g['block_reason']}")
print(f"Final Answer: {out_g['final_answer']}")

