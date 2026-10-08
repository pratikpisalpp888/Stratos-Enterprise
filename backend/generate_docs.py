"""
generate_docs.py - Generates 105 missing personal documents for 35 employees using Groq LLM
"""
import json
import os
import time
from pathlib import Path
from groq import Groq

DATA_DIR = Path(r"d:\2026\Stratos Enterprise\data\Employee_docs")
GAP_REPORT = Path(r"d:\2026\Stratos Enterprise\backend\app\ingestion\output\gap_report_missing_employees.json")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL = "llama-3.3-70b-versatile"

client = Groq(api_key=GROQ_API_KEY)

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

def call_groq(prompt, max_tokens=1200):
    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=MODEL,
                temperature=0.7,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            if attempt < 2:
                time.sleep(5)
            else:
                raise e

def generate_appraisal(emp, num):
    sal = SALARY_MAP.get(emp["role_level"], SALARY_MAP["Team Lead"])
    hike_pct = {"Director": 12, "Manager": 13, "Team Lead": 14}.get(emp["role_level"], 12)
    ctc_lpa = round(sal["ctc_annual"] / 100000, 2)
    revised_lpa = round(ctc_lpa * (1 + hike_pct / 100), 2)
    rating = {"Director": "4.4", "Manager": "4.1", "Team Lead": "3.9"}.get(emp["role_level"], "3.8")
    num_str = str(num).zfill(3)
    dept_code = DEPT_CODE_MAP[emp["department"]]
    
    prompt = f"""Write a Stratos Enterprises Performance Appraisal document. Output ONLY the document text, no preamble.

Document ID: STR-APR-{dept_code}-2025-{num_str}
Owner Employee ID: {emp["employee_id"]}
Document Type: Appraisal Record
Sensitivity Level: Confidential
Access Roles: {emp["employee_id"]}, {emp["manager_id"]}, HR-Admin
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
Reporting Manager: {emp["manager_name"]} ({emp["manager_id"]})
Employment Type: Full-Time
Join Date: [pick a realistic date 2013-2020 appropriate for {emp["role_level"]}]


Performance Rating Summary

Overall Rating: {rating} out of 5
Rating Category: {"Exceeds Expectations" if float(rating) >= 4.0 else "Meets Expectations"}


Key Achievements

[Write 3 specific achievements for a {emp["designation"]} at Stratos Enterprises, a SaaS/cloud company. Each 2-3 sentences. Include numbers/metrics.]


Areas of Improvement

[Write 2 specific improvement areas for this role, 2-3 sentences each.]


Manager Comments

{emp["manager_name"]}:

[Write 3-4 sentences of realistic manager commentary for a {emp["role_level"]} reviewing a {emp["designation"]}. Be specific to Stratos Enterprise context.]


Salary Hike Recommendation

Current CTC: {ctc_lpa} LPA
Recommended Hike: {hike_pct} percent
Revised CTC: {revised_lpa} LPA
Effective Date: August 1 2025

Justification: [One sentence justification]


Signatures

Reporting Manager: {emp["manager_name"]}
Date: 2025-07-08

HR Representative: Sunita Krishnamurthy
Date: 2025-07-10

This document is strictly confidential and intended only for the employee, their reporting manager, and authorized HR personnel. Unauthorized access or disclosure is a violation of Stratos Enterprises HR Policy HR-POL-2023-Rev3.

END OF DOCUMENT STR-APR-{dept_code}-2025-{num_str}"""

    return call_groq(prompt, 1300)

def generate_salary_slip(emp):
    sal = SALARY_MAP.get(emp["role_level"], SALARY_MAP["Team Lead"])
    gross = sal["basic"] + sal["hra"] + sal["allowance"] + sal["bonus"]
    pf = round(sal["basic"] * 0.12)
    prof_tax = 200
    tds = {"Director": 95000, "Manager": 38000, "Team Lead": 18000}.get(emp["role_level"], 18000)
    total_ded = pf + prof_tax + tds
    net = gross - total_ded
    monthly_ctc = round(sal["ctc_annual"] / 12)
    pan_suffix = str(abs(hash(emp["employee_id"] + "pan")))[-4:]
    acc_suffix = str(abs(hash(emp["employee_id"] + "acc")))[-4:]
    join_year = {"Director": "2013", "Manager": "2017", "Team Lead": "2019"}.get(emp["role_level"], "2020")
    
    content = f"""---METADATA---
Owner_Employee_ID: {emp["employee_id"]}
Owner_Name: {emp["full_name"]}
Department: {emp["department"]}
Document_Type: Salary Slip
Sensitivity_Level: Restricted
Access_Roles: {emp["employee_id"]}, {emp["manager_id"]}, Finance-Admin, HR-Admin
---END METADATA---

STRATOS ENTERPRISES PRIVATE LIMITED
SALARY SLIP FOR THE MONTH OF SEPTEMBER 2025
CONFIDENTIAL

Employee Details

Employee Name       : {emp["full_name"]}
Employee ID         : {emp["employee_id"]}
Department          : {emp["department"]}
Designation         : {emp["designation"]}
Role Level          : {emp["role_level"]}
Location            : Bangalore
Date of Joining     : {join_year}-06-01
PAN                 : ABCXX{pan_suffix}X
Bank Account        : XXXX XXXX XXXX {acc_suffix}
Pay Period          : September 2025
Payment Date        : September 30 2025
Working Days        : 26 of 26


Earnings

Basic Salary                        : INR {sal["basic"]:,}
House Rent Allowance (HRA)          : INR {sal["hra"]:,}
Special Allowance                   : INR {sal["allowance"]:,}
Performance Bonus                   : INR {sal["bonus"]:,}
Gross Salary                        : INR {gross:,}


Deductions

Provident Fund (Employee 12 percent): INR {pf:,}
Professional Tax                    : INR {prof_tax}
Income Tax (TDS)                    : INR {tds:,}
Total Deductions                    : INR {total_ded:,}


Net Salary (Take Home)              : INR {net:,}


Salary Breakup Note

Annual CTC                          : INR {sal["ctc_annual"]:,}
Monthly CTC                         : INR {monthly_ctc:,}
Effective from August 1 2025 post appraisal increment.


This salary slip is system generated and does not require a physical
signature. For queries contact payroll@stratosenterprises.com

Stratos Enterprises Private Limited
Registered Office: 14th Floor, Prestige Tower, MG Road, Bangalore 560001

This document is strictly confidential and restricted to the named
employee, their reporting manager, Finance Admin, and HR Admin only.
Unauthorized access is a violation of Stratos Enterprises HR Policy.

END OF DOCUMENT STX-SAL-{emp["employee_id"].replace("-", "")}-SEP2025"""
    return content

def generate_leave_record(emp):
    emp_id_clean = emp["employee_id"].replace("-", "")
    prompt = f"""Write a Stratos Enterprises Leave History Record. Output ONLY the document text, no preamble or explanation.

---METADATA---
Owner_Employee_ID: {emp["employee_id"]}
Owner_Name: {emp["full_name"]}
Department: {emp["department"]}
Document_Type: Leave History Record
Sensitivity_Level: Internal
Access_Roles: {emp["employee_id"]}, {emp["manager_id"]}, HR-Admin
---END METADATA---

STRATOS ENTERPRISES PRIVATE LIMITED
LEAVE HISTORY RECORD 2025
INTERNAL DOCUMENT

Employee Details

Employee Name       : {emp["full_name"]}
Employee ID         : {emp["employee_id"]}
Department          : {emp["department"]}
Designation         : {emp["designation"]}
Reporting Manager   : {emp["manager_name"]} ({emp["manager_id"]})
Location            : Bangalore
Leave Year          : January 2025 to December 2025


Leave Balance Summary

Leave Type          Allotted    Used    Pending    Remaining
Annual Leave        18          [X]     [X]        [X]
Casual Leave        8           [X]     [X]        [X]
Sick Leave          10          [X]     [X]        [X]
Total               36          [X]     [X]        [X]


Leave History

[Write exactly 4 leave entries spread across Jan-Oct 2025, using this format for each:

Entry N
Leave Type          : [Annual Leave / Casual Leave / Sick Leave]
From Date           : [YYYY-MM-DD]
To Date             : [YYYY-MM-DD]
Duration            : [N] Days
Reason              : [realistic reason]
Status              : Approved
Applied On          : [YYYY-MM-DD]
Approved By         : {emp["manager_name"]}, {emp["designation"]}
Approved On         : [YYYY-MM-DD]
]


Current Leave Balance as of October 2025

Annual Leave Remaining    : [X] Days
Casual Leave Remaining    : [X] Days
Sick Leave Remaining      : [X] Days
Total Remaining           : [X] Days

Note: Unused Annual Leave up to a maximum of 10 days will be carried
forward to 2026 as per Stratos Enterprises Leave Policy LP-2023-Rev2.
Remaining Casual and Sick Leave will lapse on December 31 2025.

For leave related queries contact hroperations@stratosenterprises.com

END OF DOCUMENT STX-LVH-{emp_id_clean}-2025"""

    return call_groq(prompt, 1000)

def main():
    with open(GAP_REPORT, "r", encoding="utf-8") as f:
        employees = json.load(f)

    created_files = []
    errors = []
    appraisal_counters = {}

    for idx, emp in enumerate(employees):
        print(f"[{idx+1}/35] {emp['full_name']} ({emp['employee_id']}) - {emp['department']}")
        dept = emp["department"]

        if dept not in appraisal_counters:
            appraisal_counters[dept] = get_next_appraisal_num(dept)

        # APPRAISAL
        try:
            num = appraisal_counters[dept]
            content = generate_appraisal(emp, num)
            appraisal_counters[dept] += 1
            folder = DATA_DIR / "Appraisals" / DEPT_FOLDER_MAP[dept]
            fname = f"STR-APR-{DEPT_CODE_MAP[dept]}-2025-{str(num).zfill(3)}.txt"
            (folder / fname).write_text(content, encoding="utf-8")
            created_files.append(fname)
            print(f"  APR OK: {fname}")
        except Exception as e:
            errors.append(f"APR {emp['employee_id']}: {e}")
            print(f"  APR FAIL: {e}")
        time.sleep(1.5)

        # SALARY SLIP
        try:
            content = generate_salary_slip(emp)
            folder = DATA_DIR / "Salary_slips" / dept
            fname = f"{emp['full_name']}.txt"
            (folder / fname).write_text(content, encoding="utf-8")
            created_files.append(fname)
            print(f"  SAL OK: {fname}")
        except Exception as e:
            errors.append(f"SAL {emp['employee_id']}: {e}")
            print(f"  SAL FAIL: {e}")
        time.sleep(0.5)

        # LEAVE RECORD
        try:
            content = generate_leave_record(emp)
            folder = DATA_DIR / "Leave Records" / dept
            fname = f"{emp['full_name']}.txt"
            (folder / fname).write_text(content, encoding="utf-8")
            created_files.append(fname)
            print(f"  LVH OK: {fname}")
        except Exception as e:
            errors.append(f"LVH {emp['employee_id']}: {e}")
            print(f"  LVH FAIL: {e}")
        time.sleep(1.5)

    print(f"\nDONE. Created: {len(created_files)} | Errors: {len(errors)}")
    if errors:
        for e in errors:
            print(f"  ERR: {e}")

    with open(r"d:\2026\Stratos Enterprise\backend\doc_generation_summary.json", "w") as f:
        json.dump({"created_count": len(created_files), "created": created_files, "errors": errors}, f, indent=2)

if __name__ == "__main__":
    main()
