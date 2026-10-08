import os
import json
from pathlib import Path
from collections import defaultdict

data_dir = Path(r"d:\2026\Stratos Enterprise\data")

# --- FIX 1 ---
print("=== FIX 1: Correcting Department Anomaly ===")
hr_doc = data_dir / "department_docs" / "STR-HR-Q3-2025-004.txt"
if hr_doc.exists():
    content = hr_doc.read_text(encoding="utf-8")
    if "Department: HR People Operations" in content:
        content = content.replace("Department: HR People Operations", "Department: HR")
        hr_doc.write_text(content, encoding="utf-8")
        print(f"Corrected {hr_doc.name}. New header preview:")
        print("\n".join(content.split("\n")[:10]))
    else:
        print(f"Already corrected or not found in {hr_doc.name}")

# --- FIX 2 ---
print("\n=== FIX 2: Adding Document_Type to Appraisals ===")
appraisals_dir = data_dir / "Employee_docs" / "Appraisals"
modified_count = 0
for root, _, files in os.walk(appraisals_dir):
    for file in files:
        if file.endswith(".txt"):
            fpath = Path(root) / file
            text = fpath.read_text(encoding="utf-8")
            if "Document Type:" not in text and "Document_Type:" not in text:
                lines = text.split("\n")
                new_lines = []
                inserted = False
                for line in lines:
                    new_lines.append(line)
                    if not inserted and (line.startswith("Department:") or line.startswith("Owner Employee ID:")):
                        new_lines.append("Document Type: Appraisal Record")
                        inserted = True
                if not inserted:
                    new_lines.insert(0, "Document Type: Appraisal Record")
                fpath.write_text("\n".join(new_lines), encoding="utf-8")
                modified_count += 1
print(f"Modified {modified_count} appraisal files.")

# --- FIX 4 & 5: Gap Report Data Collection ---
print("\n=== FIX 4 & 5: Gap Report Generation ===")
roster_dir = data_dir / "Employee_roaster"
all_employees = set()
if roster_dir.exists():
    for root, _, files in os.walk(roster_dir):
        for file in files:
            if file.endswith(".json"):
                data = json.load(open(Path(root) / file, 'r', encoding='utf-8'))
                for emp in data:
                    all_employees.add(emp['employee_id'])

# Track docs per employee
employee_docs = defaultdict(set)
emp_docs_dir = data_dir / "Employee_docs"

# Helper to get Owner_Employee_ID from file
def get_owner_id(fpath):
    text = fpath.read_text(encoding="utf-8")
    for line in text.split("\n")[:25]:
        if "Owner Employee ID:" in line or "Owner_Employee_ID:" in line:
            return line.split(":", 1)[1].strip()
    return None

for root, _, files in os.walk(emp_docs_dir):
    for file in files:
        if file.endswith(".txt"):
            fpath = Path(root) / file
            cat = None
            if "Appraisals" in root: cat = "appraisal"
            elif "Leave Records" in root: cat = "leave_record"
            elif "Salary_slips" in root: cat = "salary_slip"
            
            owner_id = get_owner_id(fpath)
            if owner_id:
                employee_docs[owner_id].add(cat)

full_coverage = []
partial_coverage = []

for emp_id in all_employees:
    docs = employee_docs.get(emp_id, set())
    if len(docs) == 3:
        full_coverage.append(emp_id)
    else:
        missing = []
        if "appraisal" not in docs: missing.append("appraisal")
        if "leave_record" not in docs: missing.append("leave_record")
        if "salary_slip" not in docs: missing.append("salary_slip")
        partial_coverage.append((emp_id, missing))

print(f"Employees fully covered: {len(full_coverage)}")
print(f"Employees partially covered/missing docs: {len(partial_coverage)}")

# Write FIX 4 to a file to show user later
with open('fix4_report.json', 'w') as f:
    json.dump({"full": full_coverage, "partial": partial_coverage}, f, indent=2)

print("\n--- FIX 5: Department Docs ---")
dept_docs_dir = data_dir / "department_docs"
for root, _, files in os.walk(dept_docs_dir):
    for file in files:
        if file.endswith(".txt"):
            fpath = Path(root) / file
            text = fpath.read_text(encoding="utf-8")
            dept, doc_type = "Unknown", "Unknown"
            for line in text.split("\n")[:25]:
                if line.startswith("Department:"): dept = line.split(":", 1)[1].strip()
                if line.startswith("Document Type:") or line.startswith("Document_Type:"): doc_type = line.split(":", 1)[1].strip()
            print(f"- {file} | Department: {dept} | Type: {doc_type}")
