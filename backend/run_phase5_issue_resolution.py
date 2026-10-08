from app.rbac.user_context import load_user_context
from app.retrieval.hybrid_retriever import hybrid_search

print("================================================================================")
print("ISSUE 1 TEST: RANKING FIX VERIFICATION")
print("User: Abhishek Pandey (STX-HR-002, HR Manager)")
print("================================================================================")

hr_mgr = load_user_context("STX-HR-002")

q1 = "employee appraisal performance rating"
res_q1 = hybrid_search(q1, hr_mgr, limit=5)
print(f"\nQUERY 1: '{q1}'")
print(f"Classified Intent: {res_q1['intent_classification']['intent']}")
print("Top 5 Results:")
for idx, r in enumerate(res_q1["results"]):
    p = r["payload"]
    owner = f"Owner: {p['owner_name']} ({p['owner_employee_id']})" if p.get('owner_employee_id') else "No Owner"
    print(f"  [{idx+1}] FinalScore: {r['final_score']} (RRF: {r['rrf_score']} x {r['intent_multiplier']}) | Type: {p['document_type']} | {owner}")

q2 = "what is our appraisal policy"
res_q2 = hybrid_search(q2, hr_mgr, limit=5)
print(f"\nQUERY 2: '{q2}'")
print(f"Classified Intent: {res_q2['intent_classification']['intent']}")
print("Top 5 Results:")
for idx, r in enumerate(res_q2["results"]):
    p = r["payload"]
    owner = f"Owner: {p['owner_name']} ({p['owner_employee_id']})" if p.get('owner_employee_id') else "No Owner"
    print(f"  [{idx+1}] FinalScore: {r['final_score']} (RRF: {r['rrf_score']} x {r['intent_multiplier']}) | Type: {p['document_type']} | {owner}")

print("\n================================================================================")
print("ISSUE 2 TEST: ADVERSARIAL BM25 LEAKAGE CHECK")
print("User: Meera Nair (STX-E-010, Engineering Employee)")
print("Query: 'Raghav Bansal salary breakdown deductions'")
print("================================================================================")

meera = load_user_context("STX-E-010")
res_adv = hybrid_search("Raghav Bansal salary breakdown deductions", meera, limit=20)
results_list = res_adv["results"]

raghav_sal_slips = [r for r in results_list if r["payload"].get("owner_employee_id") == "STX-F-001"]
other_people_sal_slips = [r for r in results_list if r["payload"].get("document_type") == "Salary Slip" and r["payload"].get("owner_employee_id") != "STX-E-010"]

print(f"Total results returned (limit=20): {len(results_list)}")
print(f"Raghav Bansal (STX-F-001) docs returned: {len(raghav_sal_slips)}")
print(f"Salary Slips of other employees returned: {len(other_people_sal_slips)}")

if len(raghav_sal_slips) == 0 and len(other_people_sal_slips) == 0:
    print("\nRESULT: PASS (Zero data leakage! BM25 candidate RBAC filtering blocked Raghav Bansal's salary slip before fusion.)")
else:
    print("\nRESULT: FAIL (LEAKAGE DETECTED!)")
    for r in raghav_sal_slips:
        print("  LEAKED:", r)

