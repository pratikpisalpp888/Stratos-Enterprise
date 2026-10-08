import json
from pathlib import Path
from collections import Counter

ROSTER_DIR = Path(r"d:\2026\Stratos Enterprise\data\Employee_roaster")

all_employees = []
for f in sorted(ROSTER_DIR.glob("*.json")):
    data = json.load(open(f, encoding="utf-8"))
    print(f"{f.name}: {len(data)} employees")
    all_employees.extend(data)

print(f"\nTotal employees across all roster files: {len(all_employees)}")

# Check for duplicate IDs across files
id_counts = Counter(e["employee_id"] for e in all_employees)
dups = {k: v for k, v in id_counts.items() if v > 1}
print(f"Duplicate employee_ids across files: {len(dups)}")
if dups:
    for eid, cnt in dups.items():
        print(f"  {eid}: appears {cnt} times")

# Count by department
dept_counts = Counter(e["department"] for e in all_employees)
print(f"\nEmployees per department:")
for dept, cnt in sorted(dept_counts.items()):
    print(f"  {dept}: {cnt}")

# Count by role_level
role_counts = Counter(e["role_level"] for e in all_employees)
print(f"\nEmployees per role_level:")
for role, cnt in sorted(role_counts.items()):
    print(f"  {role}: {cnt}")
