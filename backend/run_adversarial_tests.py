import json
from pathlib import Path
from app.rbac.user_context import load_user_context, _get_roster
from app.rbac.access_control import search_with_rbac

roster = _get_roster()

print("================================================================================")
print("TEST SET 1: HR Manager (Abhishek Pandey - STX-HR-002) Limit=20 Analysis")
print("================================================================================")
hr_mgr = load_user_context("STX-HR-002")
res_1 = search_with_rbac("employee appraisal performance rating", hr_mgr, limit=20)
print(f"Total returned: {len(res_1)}")
for idx, r in enumerate(res_1):
    owner = f"Owner: {r['owner_name']} ({r['owner_employee_id']})" if r['owner_employee_id'] else "No Owner"
    print(f" [{idx+1}] Score: {r['score']} | Type: {r['document_type']} | Dept: {r['department']} | Sens: {r['sensitivity_level']} | {owner}")

print("\n================================================================================")
print("TEST SET 2a: Meera Nair (STX-E-010) Salary Leak Check (limit=20)")
print("================================================================================")
meera = load_user_context("STX-E-010")
res_2a = search_with_rbac("salary breakdown deductions", meera, limit=20)
sal_slips = [r for r in res_2a if r["document_type"] == "Salary Slip"]
other_sal_slips = [r for r in sal_slips if r["owner_employee_id"] != "STX-E-010"]
print(f"Total Salary Slips returned: {len(sal_slips)}")
print(f"Salary Slips belonging to OTHERS: {len(other_sal_slips)}")
for r in res_2a:
    owner = f"Owner: {r['owner_name']} ({r['owner_employee_id']})" if r['owner_employee_id'] else "No Owner"
    print(f"  Type: {r['document_type']} | Sens: {r['sensitivity_level']} | {owner}")

print("\n================================================================================")
print("TEST SET 2b: Kunal Mehta (STX-F-005, Finance TL) Engineering Budget Check (limit=20)")
print("================================================================================")
kunal = load_user_context("STX-F-005")
res_2b = search_with_rbac("quarterly budget report Engineering", kunal, limit=20)
eng_restricted = [r for r in res_2b if r["department"] == "Engineering" and r["sensitivity_level"] == "Restricted"]
print(f"Restricted Engineering docs returned: {len(eng_restricted)}")
for r in res_2b:
    print(f"  Type: {r['document_type']} | Dept: {r['department']} | Sens: {r['sensitivity_level']}")

print("\n================================================================================")
print("TEST SET 2c & 2e: Kunal Mehta (STX-F-005, Finance TL) Appraisal & Salary Admin Check")
print("================================================================================")
print(f"Is Kunal Finance Admin? {kunal.is_finance_admin}")
res_2c = search_with_rbac("appraisal performance rating", kunal, limit=20)
appraisals = [r for r in res_2c if r["document_type"] == "Appraisal Record"]
print(f"Total Appraisals returned: {len(appraisals)}")
# Find Finance employees who do NOT report to Kunal (Kunal's ID is STX-F-005)
non_reports = [e for e in roster.values() if e["department"] == "Finance" and e.get("manager_id") != "STX-F-005" and e["employee_id"] != "STX-F-005"]
non_report_ids = set(e["employee_id"] for e in non_reports)

leaked_appraisals = [r for r in appraisals if r["owner_employee_id"] in non_report_ids]
print(f"Appraisals of Non-Direct-Reports returned: {len(leaked_appraisals)}")
for r in appraisals:
    print(f"  Owner: {r['owner_name']} ({r['owner_employee_id']}) | Mgr: {r['manager_id']}")

res_2e = search_with_rbac("salary breakdown", kunal, limit=20)
fin_sal_slips = [r for r in res_2e if r["document_type"] == "Salary Slip"]
other_fin_sal = [r for r in fin_sal_slips if r["owner_employee_id"] != "STX-F-005" and r["manager_id"] != "STX-F-005"]
print(f"Salary Slips of Non-Direct-Reports for Team Lead: {len(other_fin_sal)}")

print("\n================================================================================")
print("TEST SET 2d: Lowest Clearance / Intern Role Check")
print("================================================================================")
# Check for Interns in roster
interns = [e for e in roster.values() if e.get("role_level") == "Intern"]
print(f"Interns found in roster: {len(interns)}")
test_emp_id = interns[0]["employee_id"] if interns else "STX-E-015" # fallback to Employee
test_user = load_user_context(test_emp_id)
print(f"Testing User: {test_user.full_name} ({test_user.employee_id}) | Role: {test_user.role_level}")

res_2d1 = search_with_rbac("salary breakdown", test_user, limit=20)
res_2d2 = search_with_rbac("quarterly budget report", test_user, limit=20)

forbidden_d1 = [r for r in res_2d1 if r["sensitivity_level"] in ["Confidential", "Restricted"] and r["owner_employee_id"] != test_user.employee_id]
forbidden_d2 = [r for r in res_2d2 if r["sensitivity_level"] in ["Confidential", "Restricted"] and r["owner_employee_id"] != test_user.employee_id]

print(f"Forbidden Confidential/Restricted docs for salary query: {len(forbidden_d1)}")
print(f"Forbidden Confidential/Restricted docs for budget query: {len(forbidden_d2)}")

