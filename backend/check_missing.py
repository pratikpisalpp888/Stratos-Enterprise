import json, os
from pathlib import Path

data_dir = Path(r"d:\2026\Stratos Enterprise\data\Employee_docs")
gap = json.load(open(r"d:\2026\Stratos Enterprise\backend\app\ingestion\output\gap_report_missing_employees.json"))

DEPT_CODE = {"Engineering":"ENG","Finance":"FIN","HR":"HR","Legal":"LEG","Sales":"SAL"}
DEPT_FOLDER = {
    "Engineering":"Engineering_dept_employees_Appraisals",
    "Finance":"Finance_dept_employees_Appraisals",
    "HR":"HR_dept_employees_Appraisals",
    "Legal":"Legal_dept_employees_Appraisals",
    "Sales":"Sales_dept_employees_Appraisals"
}

missing_retry = []
for emp in gap:
    dept = emp["department"]
    code = DEPT_CODE[dept]
    
    sal_path = data_dir / "Salary_slips" / dept / (emp["full_name"] + ".txt")
    lvh_path = data_dir / "Leave Records" / dept / (emp["full_name"] + ".txt")
    apr_folder = data_dir / "Appraisals" / DEPT_FOLDER[dept]
    apr_files = list(apr_folder.glob("STR-APR-" + code + "-2025-*.txt"))
    apr_exists = any(emp["employee_id"] in f.read_text(encoding="utf-8") for f in apr_files)
    
    missing = []
    if not apr_exists: missing.append("appraisal")
    if not lvh_path.exists(): missing.append("leave_record")
    if not sal_path.exists(): missing.append("salary_slip")
    
    if missing:
        entry = dict(emp)
        entry["still_missing"] = missing
        missing_retry.append(entry)

print("Employees still needing docs:", len(missing_retry))
for e in missing_retry:
    print(" ", e["employee_id"], e["full_name"], e["still_missing"])

with open(r"d:\2026\Stratos Enterprise\backend\retry_employees.json", "w") as f:
    json.dump(missing_retry, f, indent=2)

print("Saved retry_employees.json")
