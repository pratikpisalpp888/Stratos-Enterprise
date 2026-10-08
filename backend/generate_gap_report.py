import json
from pathlib import Path
import os

data_dir = Path(r"d:\2026\Stratos Enterprise\data")
roster_dir = data_dir / "Employee_roaster"
backend_dir = Path(r"d:\2026\Stratos Enterprise\backend")
fix4_path = backend_dir / "fix4_report.json"
output_path = backend_dir / "app" / "ingestion" / "output" / "gap_report_missing_employees.json"

# Load fix4 report
with open(fix4_path, 'r', encoding='utf-8') as f:
    fix4_data = json.load(f)

partial_coverage = fix4_data.get("partial", [])

# Load all employees
all_employees = {}
if roster_dir.exists():
    for root, _, files in os.walk(roster_dir):
        for file in files:
            if file.endswith(".json"):
                data = json.load(open(Path(root) / file, 'r', encoding='utf-8'))
                for emp in data:
                    all_employees[emp['employee_id']] = emp

# Build final list
missing_employees = []
for item in partial_coverage:
    emp_id = item[0]
    missing_docs = item[1]
    
    if emp_id in all_employees:
        emp = all_employees[emp_id]
        manager_id = emp.get("manager_id")
        manager_name = None
        if manager_id and manager_id in all_employees:
            manager_name = all_employees[manager_id].get("full_name")
            
        record = {
            "employee_id": emp_id,
            "full_name": emp.get("full_name"),
            "department": emp.get("department"),
            "designation": emp.get("designation"),
            "role_level": emp.get("role_level"),
            "manager_id": manager_id,
            "manager_name": manager_name,
            "missing_docs": missing_docs
        }
        missing_employees.append(record)

# Ensure directory exists
output_path.parent.mkdir(parents=True, exist_ok=True)

# Write to file
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(missing_employees, f, indent=2)

print("SUCCESS")
