import json, re
from pathlib import Path

# All 7 null files
null_files = [
    r"D:\2026\Stratos Enterprise\data\Employee_docs\Appraisals\Engineering_dept_employees_Appraisals\STR-APR-ENG-2025-013.txt",
    r"D:\2026\Stratos Enterprise\data\Employee_docs\Appraisals\Finance_dept_employees_Appraisals\STR-APR-FIN-2025-007.txt",
    r"D:\2026\Stratos Enterprise\data\Employee_docs\Appraisals\Finance_dept_employees_Appraisals\STR-APR-FIN-2025-011.txt",
    r"D:\2026\Stratos Enterprise\data\Employee_docs\Appraisals\Legal_dept_employees_Appraisals\STR-APR-LEG-2025-012.txt",
    r"D:\2026\Stratos Enterprise\data\Employee_docs\Appraisals\Sales_dept_employees_Appraisals\STR-APR-SAL-2025-010.txt",
]

# Also load all chunks to find remaining 2 null files
chunks = json.load(open(r"d:\2026\Stratos Enterprise\backend\app\ingestion\output\processed_chunks.json"))
null_sources = set(c["source_file"] for c in chunks if not c["metadata"].get("Sensitivity_Level"))
null_files = sorted(null_sources)
print(f"All {len(null_files)} null files:")
for f in null_files:
    print(f"  {f}")

fixed = 0
for fpath in null_files:
    p = Path(fpath)
    content = p.read_text(encoding="utf-8")
    
    # Extract fields from content
    emp_id = ""
    emp_name = ""
    dept = ""
    owner_id = ""
    manager_id = ""
    
    for line in content.split("\n"):
        line = line.strip()
        if line.startswith("Employee ID:"):
            emp_id = line.split(":", 1)[1].strip()
        elif line.startswith("Employee Name:"):
            emp_name = line.split(":", 1)[1].strip()
        elif line.startswith("Department:"):
            dept = line.split(":", 1)[1].strip()
        elif line.startswith("Reporting Manager:"):
            # Extract manager ID from parentheses e.g. "Karthik Reddy (STX-E-003)"
            m = re.search(r"\((STX-[A-Z0-9\-]+)\)", line)
            if m:
                manager_id = m.group(1)
    
    if not emp_id:
        print(f"  SKIP - could not extract emp_id from {p.name}")
        continue
    
    header = (
        f"Document ID: {p.stem}\n"
        f"Owner Employee ID: {emp_id}\n"
        f"Document Type: Appraisal Record\n"
        f"Sensitivity Level: Confidential\n"
        f"Access Roles: {emp_id}, {manager_id}, HR-Admin\n"
        f"Department: {dept}\n"
        f"Review Period: January 2025 to June 2025\n"
        f"Created Date: 2025-07-10\n"
        f"Prepared By: HR People Operations\n\n"
    )
    
    new_content = header + content
    p.write_text(new_content, encoding="utf-8")
    print(f"  FIXED: {p.name} -> emp_id={emp_id}, dept={dept}, manager={manager_id}")
    fixed += 1

print(f"\nFixed {fixed} files.")
