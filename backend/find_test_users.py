import json
from pathlib import Path

roster_dir = Path(r"d:\2026\Stratos Enterprise\data\Employee_roaster")
employees = []
for f in roster_dir.glob("*.json"):
    employees.extend(json.load(open(f, encoding="utf-8")))

# Find test candidates
print("=== INTERN/EMPLOYEE in Engineering ===")
for e in employees:
    if e["department"] == "Engineering" and e["role_level"] == "Employee":
        print(f"  {e['employee_id']} | {e['full_name']} | {e['role_level']} | mgr: {e.get('manager_id')}")
        break

print("\n=== TEAM LEAD in Finance ===")
for e in employees:
    if e["department"] == "Finance" and e["role_level"] == "Team Lead":
        print(f"  {e['employee_id']} | {e['full_name']} | {e['role_level']} | mgr: {e.get('manager_id')}")
        break

print("\n=== MANAGER in HR ===")
for e in employees:
    if e["department"] == "HR" and e["role_level"] == "Manager":
        print(f"  {e['employee_id']} | {e['full_name']} | {e['role_level']} | mgr: {e.get('manager_id')}")
        break

print("\n=== DIRECTOR in Finance ===")
for e in employees:
    if e["department"] == "Finance" and e["role_level"] == "Director":
        print(f"  {e['employee_id']} | {e['full_name']} | {e['role_level']} | mgr: {e.get('manager_id')}")
        break

print("\n=== C-LEVEL or Director in any dept ===")
for e in employees:
    if e["role_level"] == "Director":
        print(f"  {e['employee_id']} | {e['full_name']} | {e['department']} | {e['role_level']}")
