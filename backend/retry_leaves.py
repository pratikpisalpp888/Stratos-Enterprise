import json, time, os
from pathlib import Path
from groq import Groq

DATA_DIR = Path(r"d:\2026\Stratos Enterprise\data\Employee_docs")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL = "llama-3.1-8b-instant"  # Fast model - separate token pool

client = Groq(api_key=GROQ_API_KEY)

employees = json.load(open(r"d:\2026\Stratos Enterprise\backend\retry_employees.json"))

def generate_leave_record(emp):
    emp_id_clean = emp["employee_id"].replace("-", "")
    prompt = (
        "Write a Stratos Enterprises Leave History Record. Output ONLY the document text.\n\n"
        "---METADATA---\n"
        "Owner_Employee_ID: " + emp["employee_id"] + "\n"
        "Owner_Name: " + emp["full_name"] + "\n"
        "Department: " + emp["department"] + "\n"
        "Document_Type: Leave History Record\n"
        "Sensitivity_Level: Internal\n"
        "Access_Roles: " + emp["employee_id"] + ", " + str(emp["manager_id"]) + ", HR-Admin\n"
        "---END METADATA---\n\n"
        "STRATOS ENTERPRISES PRIVATE LIMITED\n"
        "LEAVE HISTORY RECORD 2025\n"
        "INTERNAL DOCUMENT\n\n"
        "Employee Details\n\n"
        "Employee Name       : " + emp["full_name"] + "\n"
        "Employee ID         : " + emp["employee_id"] + "\n"
        "Department          : " + emp["department"] + "\n"
        "Designation         : " + emp["designation"] + "\n"
        "Reporting Manager   : " + str(emp["manager_name"]) + " (" + str(emp["manager_id"]) + ")\n"
        "Location            : Bangalore\n"
        "Leave Year          : January 2025 to December 2025\n\n\n"
        "Leave Balance Summary\n\n"
        "Leave Type          Allotted    Used    Pending    Remaining\n"
        "Annual Leave        18          [fill]  [fill]     [fill]\n"
        "Casual Leave        8           [fill]  [fill]     [fill]\n"
        "Sick Leave          10          [fill]  [fill]     [fill]\n"
        "Total               36          [fill]  [fill]     [fill]\n\n\n"
        "Leave History\n\n"
        "Write exactly 4 leave entries (Jan-Oct 2025). For each entry use this format:\n"
        "Entry N\n"
        "Leave Type          : [type]\n"
        "From Date           : [YYYY-MM-DD]\n"
        "To Date             : [YYYY-MM-DD]\n"
        "Duration            : [N] Days\n"
        "Reason              : [realistic reason]\n"
        "Status              : Approved\n"
        "Applied On          : [YYYY-MM-DD]\n"
        "Approved By         : " + str(emp["manager_name"]) + ", " + emp["designation"] + "\n"
        "Approved On         : [YYYY-MM-DD]\n\n\n"
        "Current Leave Balance as of October 2025\n\n"
        "Annual Leave Remaining    : [X] Days\n"
        "Casual Leave Remaining    : [X] Days\n"
        "Sick Leave Remaining      : [X] Days\n"
        "Total Remaining           : [X] Days\n\n"
        "Note: Unused Annual Leave up to a maximum of 10 days will be carried\n"
        "forward to 2026 as per Stratos Enterprises Leave Policy LP-2023-Rev2.\n"
        "Remaining Casual and Sick Leave will lapse on December 31 2025.\n\n"
        "For leave related queries contact hroperations@stratosenterprises.com\n\n"
        "END OF DOCUMENT STX-LVH-" + emp_id_clean + "-2025"
    )
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=MODEL,
                temperature=0.7,
                max_tokens=900
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            if attempt < 2:
                print(f"    Retry {attempt+1}: {e}")
                time.sleep(10)
            else:
                raise e

created = []
errors = []
for idx, emp in enumerate(employees):
    print(f"[{idx+1}/9] {emp['full_name']} ({emp['employee_id']})")
    try:
        content = generate_leave_record(emp)
        folder = DATA_DIR / "Leave Records" / emp["department"]
        fname = emp["full_name"] + ".txt"
        (folder / fname).write_text(content, encoding="utf-8")
        created.append(fname)
        print(f"  LVH OK: {fname}")
    except Exception as e:
        errors.append(str(e))
        print(f"  FAIL: {e}")
    time.sleep(2)

print(f"\nDone. Created: {len(created)} | Errors: {len(errors)}")
for e in errors:
    print(f"  ERR: {e}")
