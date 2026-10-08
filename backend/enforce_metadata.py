import json, os, re
from pathlib import Path

DATA_DIR = Path(r"d:\2026\Stratos Enterprise\data\Employee_docs")
ROSTER_DIR = Path(r"d:\2026\Stratos Enterprise\data\Employee_roaster")

# Load all valid employees
all_employees = {}
for f in ROSTER_DIR.glob("*.json"):
    for emp in json.load(open(f, encoding="utf-8")):
        all_employees[emp["employee_id"]] = emp

# Map full name to employee dict for lookup
name_to_emp = {emp["full_name"]: emp for emp in all_employees.values()}

DEPT_CODE_MAP = {
    "Engineering": "ENG", "Finance": "FIN", "HR": "HR",
    "Legal": "LEG", "Sales": "SAL"
}

def extract_field(text, key):
    m = re.search(rf"{key}\s*:\s*(.*)", text, re.IGNORECASE)
    return m.group(1).strip() if m else ""

def fix_file(fpath):
    text = fpath.read_text(encoding="utf-8")
    if "---METADATA---" in text:
        return False  # Already has metadata
        
    print(f"Fixing metadata for: {fpath.name}")
    
    # Extract info from body
    emp_id = extract_field(text, "Employee ID")
    emp_name = extract_field(text, "Employee Name")
    dept = extract_field(text, "Department")
    doc_type = extract_field(text, "Document Type")
    
    # Try other variations
    if not emp_id:
        emp_id = extract_field(text, "Owner Employee ID")
    if not emp_name:
        emp_name = extract_field(text, "Owner Name")
        
    # Resolve from roster if missing
    emp_info = None
    if emp_id in all_employees:
        emp_info = all_employees[emp_id]
    elif emp_name in name_to_emp:
        emp_info = name_to_emp[emp_name]
        
    if not emp_info:
        print(f"  ERROR: Could not resolve employee info for {fpath.name} (ID: '{emp_id}', Name: '{emp_name}')")
        return False
        
    emp_id = emp_info["employee_id"]
    emp_name = emp_info["full_name"]
    dept = emp_info["department"]
    manager_id = emp_info.get("manager_id")
    
    # Determine document type and sensitivity
    sensitivity = "Internal"
    access_roles = [emp_id, "HR-Admin"]
    
    # Check folder path or text content to find type
    path_str = str(fpath).lower()
    if "appraisal" in path_str:
        doc_type = "Appraisal Record"
        sensitivity = "Confidential"
        if manager_id:
            access_roles.insert(1, manager_id)
    elif "salary" in path_str:
        doc_type = "Salary Slip"
        sensitivity = "Restricted"
        access_roles.extend(["Finance-Admin"])
        if manager_id:
            access_roles.insert(1, manager_id)
    elif "leave" in path_str:
        doc_type = "Leave History Record"
        sensitivity = "Internal"
        if manager_id:
            access_roles.insert(1, manager_id)
            
    roles_str = ", ".join(access_roles)
    
    header = (
        "---METADATA---\n"
        f"Owner_Employee_ID: {emp_id}\n"
        f"Owner_Name: {emp_name}\n"
        f"Department: {dept}\n"
        f"Document_Type: {doc_type}\n"
        f"Sensitivity_Level: {sensitivity}\n"
        f"Access_Roles: [{roles_str}]\n"
        "---END METADATA---\n\n"
    )
    
    # Strip any half-baked headers or text at the beginning
    clean_text = text.strip()
    # If the text starts with the fields we extracted, clean them up or prepend
    # We will just write the header at the top
    fpath.write_text(header + clean_text, encoding="utf-8")
    return True

fixed_count = 0
for root, _, files in os.walk(DATA_DIR):
    for f in files:
        if f.endswith(".txt"):
            if fix_file(Path(root) / f):
                fixed_count += 1

print(f"\nSuccessfully verified and fixed {fixed_count} files.")
