import json, time, os
from pathlib import Path
from groq import Groq

DATA_DIR = Path(r"d:\2026\Stratos Enterprise\data\Employee_docs")
ROSTER_DIR = Path(r"d:\2026\Stratos Enterprise\data\Employee_roaster")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL = "llama-3.1-8b-instant"

client = Groq(api_key=GROQ_API_KEY)

# Load all valid employees to resolve manager names
all_employees = {}
for f in ROSTER_DIR.glob("*.json"):
    for emp in json.load(open(f, encoding="utf-8")):
        all_employees[emp["employee_id"]] = emp

missing_appraisals = json.load(open(r"d:\2026\Stratos Enterprise\backend\missing_appraisals.json"))

DEPT_CODE_MAP = {
    "Engineering": "ENG", "Finance": "FIN", "HR": "HR",
    "Legal": "LEG", "Sales": "SAL"
}
DEPT_FOLDER_MAP = {
    "Engineering": "Engineering_dept_employees_Appraisals",
    "Finance": "Finance_dept_employees_Appraisals",
    "HR": "HR_dept_employees_Appraisals",
    "Legal": "Legal_dept_employees_Appraisals",
    "Sales": "Sales_dept_employees_Appraisals"
}
SALARY_MAP = {
    "Director":  {"basic": 350000, "hra": 140000, "allowance": 85000, "bonus": 55000, "ctc_annual": 9500000},
    "Manager":   {"basic": 180000, "hra": 72000,  "allowance": 45000, "bonus": 28000, "ctc_annual": 4800000},
    "Team Lead": {"basic": 110000, "hra": 44000,  "allowance": 28000, "bonus": 18000, "ctc_annual": 3000000},
}

def get_next_appraisal_num(dept):
    code = DEPT_CODE_MAP[dept]
    folder = DATA_DIR / "Appraisals" / DEPT_FOLDER_MAP[dept]
    existing = list(folder.glob(f"STR-APR-{code}-2025-*.txt"))
    if not existing:
        return 7
    nums = [int(f.stem.split("-")[-1]) for f in existing]
    return max(nums) + 1

def generate_appraisal(emp, num):
    sal = SALARY_MAP.get(emp["role_level"], SALARY_MAP["Team Lead"])
    hike_pct = {"Director": 12, "Manager": 13, "Team Lead": 14}.get(emp["role_level"], 12)
    ctc_lpa = round(sal["ctc_annual"] / 100000, 2)
    revised_lpa = round(ctc_lpa * (1 + hike_pct / 100), 2)
    rating = {"Director": "4.4", "Manager": "4.1", "Team Lead": "3.9"}.get(emp["role_level"], "3.8")
    num_str = str(num).zfill(3)
    dept_code = DEPT_CODE_MAP[emp["department"]]
    
    manager_id = emp.get("manager_id")
    manager_name = "Sunita Krishnamurthy"
    if manager_id and manager_id in all_employees:
        manager_name = all_employees[manager_id]["full_name"]
    
    prompt = f"""Write a Stratos Enterprises Performance Appraisal document. Output ONLY the document text.

Document ID: STR-APR-{dept_code}-2025-{num_str}
Owner Employee ID: {emp["employee_id"]}
Document Type: Appraisal Record
Sensitivity Level: Confidential
Access Roles: {emp["employee_id"]}, {manager_id if manager_id else "HR-Admin"}, HR-Admin
Department: {emp["department"]}
Review Period: January 2025 to June 2025
Created Date: 2025-07-10
Prepared By: HR People Operations


STRATOS ENTERPRISES
PERFORMANCE APPRAISAL REPORT
REVIEW PERIOD JANUARY 2025 TO JUNE 2025
CONFIDENTIAL


Employee Information

Employee Name: {emp["full_name"]}
Employee ID: {emp["employee_id"]}
Department: {emp["department"]}
Designation: {emp["designation"]}
Location: Bangalore
Reporting Manager: {manager_name} ({manager_id})
Employment Type: Full-Time
Join Date: 2018-04-12


Performance Rating Summary

Overall Rating: {rating} out of 5
Rating Category: {"Exceeds Expectations" if float(rating) >= 4.0 else "Meets Expectations"}


Key Achievements

[Write 3 specific achievements for a {emp["designation"]} at Stratos Enterprises. Each 2-3 sentences.]


Areas of Improvement

[Write 2 specific improvement areas for this role, 2-3 sentences each.]


Manager Comments

{manager_name}:

[Write 3-4 sentences of realistic manager commentary for a {emp["role_level"]} reviewing a {emp["designation"]}.]


Salary Hike Recommendation

Current CTC: {ctc_lpa} LPA
Recommended Hike: {hike_pct} percent
Revised CTC: {revised_lpa} LPA
Effective Date: August 1 2025

Justification: High impact role execution.


Signatures

Reporting Manager: {manager_name}
Date: 2025-07-08

HR Representative: Sunita Krishnamurthy
Date: 2025-07-10

This document is strictly confidential and intended only for the employee, their reporting manager, and authorized HR personnel. Unauthorized access or disclosure is a violation of Stratos Enterprises HR Policy HR-POL-2023-Rev3.

END OF DOCUMENT STR-APR-{dept_code}-2025-{num_str}"""

    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=MODEL,
                temperature=0.7,
                max_tokens=1300
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            if attempt < 2:
                time.sleep(10)
            else:
                raise e

for idx, emp in enumerate(missing_appraisals):
    dept = emp["department"]
    num = get_next_appraisal_num(dept)
    print(f"[{idx+1}/9] Generating appraisal for {emp['full_name']} (STR-APR-{DEPT_CODE_MAP[dept]}-2025-{str(num).zfill(3)})")
    try:
        content = generate_appraisal(emp, num)
        folder = DATA_DIR / "Appraisals" / DEPT_FOLDER_MAP[dept]
        fname = f"STR-APR-{DEPT_CODE_MAP[dept]}-2025-{str(num).zfill(3)}.txt"
        (folder / fname).write_text(content, encoding="utf-8")
        print(f"  OK Saved {fname}")
    except Exception as e:
        print(f"  FAIL: {e}")
    time.sleep(2)

print("\nDone generating missing appraisals.")
