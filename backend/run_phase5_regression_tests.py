import json
from app.rbac.user_context import load_user_context, _get_roster
from app.retrieval.hybrid_retriever import hybrid_search

roster = _get_roster()

print("================================================================================")
print("PART E - REGRESSION TEST 1: SIDE-BY-SIDE RANKING FIX COMPARISON")
print("User: Abhishek Pandey (STX-HR-002, HR Manager)")
print("================================================================================")

hr_mgr = load_user_context("STX-HR-002")

q1 = "employee appraisal performance rating"
res_q1 = hybrid_search(q1, hr_mgr, limit=5)
print(f"\nQUERY 1: '{q1}'")
print(f"Classified Intent: {res_q1['intent_classification']['intent']} (confidence={res_q1['intent_classification']['confidence']})")
print(f"Top 5 Results:")
for idx, r in enumerate(res_q1["results"]):
    p = r["payload"]
    owner = f"Owner: {p['owner_name']} ({p['owner_employee_id']})" if p.get('owner_employee_id') else "No Owner"
    print(f"  [{idx+1}] FinalScore: {r['final_score']} (RRF: {r['rrf_score']} x {r['intent_multiplier']}) | DenseRank: {r['dense_rank']} | SparseRank: {r['sparse_rank']} | Type: {p['document_type']} | {owner}")

q2 = "what is our appraisal policy"
res_q2 = hybrid_search(q2, hr_mgr, limit=5)
print(f"\nQUERY 2: '{q2}'")
print(f"Classified Intent: {res_q2['intent_classification']['intent']} (confidence={res_q2['intent_classification']['confidence']})")
print(f"Top 5 Results:")
for idx, r in enumerate(res_q2["results"]):
    p = r["payload"]
    owner = f"Owner: {p['owner_name']} ({p['owner_employee_id']})" if p.get('owner_employee_id') else "No Owner"
    print(f"  [{idx+1}] FinalScore: {r['final_score']} (RRF: {r['rrf_score']} x {r['intent_multiplier']}) | DenseRank: {r['dense_rank']} | SparseRank: {r['sparse_rank']} | Type: {p['document_type']} | {owner}")

print("\n================================================================================")
print("PART E - REGRESSION TEST 2: RE-RUNNING ALL PHASE 4 NEGATIVE RBAC TESTS")
print("================================================================================")

# 2a. Meera Nair (STX-E-010) Salary Leak Check (limit=20)
meera = load_user_context("STX-E-010")
res_2a = hybrid_search("salary breakdown deductions", meera, limit=20)
sal_slips_2a = [r for r in res_2a["results"] if r["payload"].get("document_type") == "Salary Slip"]
leaked_2a = [r for r in sal_slips_2a if r["payload"].get("owner_employee_id") != "STX-E-010"]
status_2a = "PASS" if len(leaked_2a) == 0 else "FAIL"
print(f"Test 2a (Meera Salary Leak): {status_2a} (Leaked salary slips of others: {len(leaked_2a)})")

# 2b. Kunal Mehta (STX-F-005, Finance TL) Engineering Budget Check (limit=20)
kunal = load_user_context("STX-F-005")
res_2b = hybrid_search("quarterly budget report Engineering", kunal, limit=20)
eng_restricted_2b = [r for r in res_2b["results"] if r["payload"].get("department") == "Engineering" and r["payload"].get("sensitivity_level") == "Restricted"]
status_2b = "PASS" if len(eng_restricted_2b) == 0 else "FAIL"
print(f"Test 2b (Kunal Engineering Budget Leak): {status_2b} (Restricted Eng docs returned: {len(eng_restricted_2b)})")

# 2c. Kunal Mehta (STX-F-005) Appraisal Leak Check (limit=20)
res_2c = hybrid_search("appraisal performance rating", kunal, limit=20)
appraisals_2c = [r for r in res_2c["results"] if r["payload"].get("document_type") == "Appraisal Record"]
non_report_ids = set(e["employee_id"] for e in roster.values() if e["department"] == "Finance" and e.get("manager_id") != "STX-F-005" and e["employee_id"] != "STX-F-005")
leaked_2c = [r for r in appraisals_2c if r["payload"].get("owner_employee_id") in non_report_ids]
status_2c = "PASS" if len(leaked_2c) == 0 else "FAIL"
print(f"Test 2c (Kunal Non-Team Appraisal Leak): {status_2c} (Leaked non-team appraisals: {len(leaked_2c)})")

# 2d. Lowest Clearance Employee Check (STX-E-015)
nikhil = load_user_context("STX-E-015")
res_2d1 = hybrid_search("salary breakdown", nikhil, limit=20)
res_2d2 = hybrid_search("quarterly budget report", nikhil, limit=20)
forbidden_2d1 = [r for r in res_2d1["results"] if r["payload"].get("sensitivity_level") in ["Confidential", "Restricted"] and r["payload"].get("owner_employee_id") != "STX-E-015"]
forbidden_2d2 = [r for r in res_2d2["results"] if r["payload"].get("sensitivity_level") in ["Confidential", "Restricted"] and r["payload"].get("owner_employee_id") != "STX-E-015"]
status_2d = "PASS" if (len(forbidden_2d1) == 0 and len(forbidden_2d2) == 0) else "FAIL"
print(f"Test 2d (Employee Confidential/Restricted Leak): {status_2d} (Forbidden salary: {len(forbidden_2d1)}, Forbidden budget: {len(forbidden_2d2)})")

# 2e. Finance Team Lead Admin Check (STX-F-005)
res_2e = hybrid_search("salary breakdown", kunal, limit=20)
fin_sal_slips_2e = [r for r in res_2e["results"] if r["payload"].get("document_type") == "Salary Slip"]
other_fin_sal_2e = [r for r in fin_sal_slips_2e if r["payload"].get("owner_employee_id") != "STX-F-005" and r["payload"].get("manager_id") != "STX-F-005"]
status_2e = "PASS" if len(other_fin_sal_2e) == 0 else "FAIL"
print(f"Test 2e (Team Lead Admin Privilege Leak): {status_2e} (Non-team salary slips: {len(other_fin_sal_2e)})")

print("\n================================================================================")
print("ALL PHASE 5 REGRESSION TESTS COMPLETED.")
print("================================================================================")
