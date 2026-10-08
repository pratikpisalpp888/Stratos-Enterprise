from pathlib import Path

# Fix 1: Rohan Pillai leave record - view content to understand format issue
rp = Path(r"D:\2026\Stratos Enterprise\data\Employee_docs\Leave Records\Legal\Rohan Pillai.txt")
content = rp.read_text(encoding="utf-8")
lines = content.split("\n")
print("=== Rohan Pillai.txt first 20 lines ===")
for i, l in enumerate(lines[:20]):
    print(f"{i}: {repr(l)}")

# Fix 2: Raghav Bansal appraisal - Director has no manager, fix Access Roles
fin_apr = Path(r"D:\2026\Stratos Enterprise\data\Employee_docs\Appraisals\Finance_dept_employees_Appraisals\STR-APR-FIN-2025-007.txt")
content2 = fin_apr.read_text(encoding="utf-8")
# Fix empty manager_id in Access Roles line
content2 = content2.replace("Access Roles: STX-F-001, , HR-Admin", "Access Roles: STX-F-001, HR-Admin, Finance-Admin")
fin_apr.write_text(content2, encoding="utf-8")
print("\nFixed Finance Director appraisal Access Roles.")
