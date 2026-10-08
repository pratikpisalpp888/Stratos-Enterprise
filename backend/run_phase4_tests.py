import json
from app.rbac.user_context import load_user_context
from app.rbac.access_control import search_with_rbac

test_users = [
    ("STX-E-010", "1. Engineering Employee"),
    ("STX-F-005", "2. Finance Team Lead"),
    ("STX-HR-002", "3. HR Manager"),
    ("STX-F-001", "4. Finance Director"),
    ("STX-L-001", "5. Legal Director (Executive/C-Level)")
]

queries = [
    ("a) salary breakdown and deductions", "salary breakdown and deductions"),
    ("b) employee appraisal performance rating", "employee appraisal performance rating"),
    ("c) quarterly budget report", "quarterly budget report")
]

all_results = {}

for eid, user_label in test_users:
    user = load_user_context(eid)
    print(f"\n================================================================================")
    print(f"USER: {user_label} | ID: {user.employee_id} | Name: {user.full_name}")
    print(f"Dept: {user.department} | Role: {user.role_level} | Clearance: {user.clearance_level}")
    print(f"================================================================================")
    
    user_results = {}
    for q_label, q_str in queries:
        res = search_with_rbac(query=q_str, user=user, limit=5)
        user_results[q_label] = res
        
        # Summarize results
        doc_types = [r["document_type"] or "Unknown" for r in res]
        depts = [r["department"] or "Personal/None" for r in res]
        sens = [r["sensitivity_level"] or "Unknown" for r in res]
        owners = [r["owner_employee_id"] for r in res if r["owner_employee_id"]]
        
        print(f"\n  QUERY: '{q_str}'")
        print(f"  Count: {len(res)} results returned")
        if res:
          for idx, item in enumerate(res):
              owner_info = f", Owner: {item['owner_name']} ({item['owner_employee_id']})" if item['owner_employee_id'] else ""
              print(f"    [{idx+1}] Score: {item['score']} | Type: {item['document_type']} | Dept: {item['department']} | Sens: {item['sensitivity_level']}{owner_info}")
        else:
          print("    [NO MATCHES / RESTRICTED]")

with open(r"d:\2026\Stratos Enterprise\backend\phase4_results.json", "w", encoding="utf-8") as f:
    json.dump(all_results, f, indent=2)

