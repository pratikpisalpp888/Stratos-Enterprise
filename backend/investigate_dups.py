import json, os, re
from pathlib import Path
from collections import defaultdict

DATA_DIR = Path(r"d:\2026\Stratos Enterprise\data\Employee_docs")
ROSTER_DIR = Path(r"d:\2026\Stratos Enterprise\data\Employee_roaster")

# Load all valid employee IDs
valid_ids = set()
valid_names = {}
for f in ROSTER_DIR.glob("*.json"):
    for emp in json.load(open(f, encoding="utf-8")):
        valid_ids.add(emp["employee_id"])
        valid_names[emp["employee_id"]] = emp["full_name"]

print(f"Total valid employees in roaster: {len(valid_ids)}")

def extract_owner_id(filepath):
    """Extract Owner_Employee_ID from file content - try multiple formats."""
    text = open(filepath, encoding="utf-8").read()
    # Try ---METADATA--- block first
    m = re.search(r"Owner_Employee_ID\s*:\s*(STX-[\w-]+)", text)
    if m: return m.group(1).strip()
    # Try flat header format
    m = re.search(r"Owner Employee ID\s*:\s*(STX-[\w-]+)", text)
    if m: return m.group(1).strip()
    # Try employee ID line in body
    m = re.search(r"Employee ID\s*:\s*(STX-[\w-]+)", text)
    if m: return m.group(1).strip()
    return None

def scan_folder(folder_name, subfolder_style):
    """Scan folder and return dict: {owner_id -> [file_paths]}"""
    base = DATA_DIR / folder_name
    owner_to_files = defaultdict(list)
    unresolved = []
    
    for root, _, files in os.walk(base):
        for fname in files:
            if fname.endswith(".txt"):
                fpath = Path(root) / fname
                owner_id = extract_owner_id(fpath)
                if owner_id:
                    owner_to_files[owner_id].append(str(fpath))
                else:
                    unresolved.append(str(fpath))
    return owner_to_files, unresolved

print("\n" + "="*60)
print("SCANNING ALL 3 DOCUMENT TYPE FOLDERS")
print("="*60)

results = {}
for folder, label in [("Appraisals", "appraisal"), ("Salary_slips", "salary_slip"), ("Leave Records", "leave_record")]:
    owner_map, unresolved = scan_folder(folder, label)
    
    duplicates = {k: v for k, v in owner_map.items() if len(v) > 1}
    orphans = {k: v for k, v in owner_map.items() if k not in valid_ids}
    
    print(f"\n--- {label.upper()} ---")
    print(f"  Total unique owner IDs found: {len(owner_map)}")
    print(f"  Total files found: {sum(len(v) for v in owner_map.values())}")
    print(f"  Duplicates (>1 file per employee): {len(duplicates)}")
    print(f"  Orphan IDs (not in roaster): {len(orphans)}")
    print(f"  Unresolved (no owner ID found): {len(unresolved)}")
    
    if duplicates:
        print(f"\n  DUPLICATES:")
        for emp_id, files in sorted(duplicates.items()):
            name = valid_names.get(emp_id, "?")
            print(f"    {emp_id} ({name}):")
            for f in files:
                print(f"      - {Path(f).name}")
    
    if orphans:
        print(f"\n  ORPHAN IDs:")
        for emp_id, files in sorted(orphans.items()):
            print(f"    {emp_id}: {[Path(f).name for f in files]}")
    
    if unresolved:
        print(f"\n  UNRESOLVED FILES (no owner ID):")
        for f in unresolved:
            print(f"    - {Path(f).name}")
    
    results[label] = {"owner_map": dict(owner_map), "duplicates": duplicates, "orphans": orphans}

# Save for next step
with open(r"d:\2026\Stratos Enterprise\backend\dup_report.json", "w") as f:
    json.dump({k: {"duplicates": {eid: fps for eid, fps in v["duplicates"].items()},
                   "orphans": {eid: fps for eid, fps in v["orphans"].items()}}
               for k, v in results.items()}, f, indent=2)
print("\nSaved dup_report.json")
