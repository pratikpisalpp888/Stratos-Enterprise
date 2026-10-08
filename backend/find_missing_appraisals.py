import json, os, re
from pathlib import Path

DATA_DIR = Path(r"d:\2026\Stratos Enterprise\data\Employee_docs")
ROSTER_DIR = Path(r"d:\2026\Stratos Enterprise\data\Employee_roaster")

# Load all valid employee IDs
valid_employees = {}
for f in ROSTER_DIR.glob("*.json"):
    for emp in json.load(open(f, encoding="utf-8")):
        valid_employees[emp["employee_id"]] = emp

# Helper to parse owner from appraisal
def get_appraisal_owner(fpath):
    text = fpath.read_text(encoding="utf-8")
    # Try metadata Owner_Employee_ID
    m = re.search(r"Owner_Employee_ID\s*:\s*(STX-[\w-]+)", text)
    if m: return m.group(1).strip()
    m = re.search(r"Owner Employee ID\s*:\s*(STX-[\w-]+)", text)
    if m: return m.group(1).strip()
    # Try Employee ID in body
    m = re.search(r"Employee ID\s*:\s*(STX-[\w-]+)", text)
    if m: return m.group(1).strip()
    return None

# Find all appraisals and their owners
appraisal_owners = {}
for root, _, files in os.walk(DATA_DIR / "Appraisals"):
    for file in files:
        if file.endswith(".txt"):
            fpath = Path(root) / file
            owner = get_appraisal_owner(fpath)
            if owner:
                appraisal_owners[owner] = str(fpath)

missing_appraisals = []
for emp_id, emp in valid_employees.items():
    if emp_id not in appraisal_owners:
        missing_appraisals.append(emp)

print("Employees missing appraisal:")
for emp in missing_appraisals:
    print(f"  {emp['employee_id']} - {emp['full_name']} ({emp['department']})")

with open(r"d:\2026\Stratos Enterprise\backend\missing_appraisals.json", "w") as f:
    json.dump(missing_appraisals, f, indent=2)
