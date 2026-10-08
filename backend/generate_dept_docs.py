import json, time, os
from pathlib import Path
from groq import Groq

ROSTER_DIR = Path(r"d:\2026\Stratos Enterprise\data\Employee_roaster")
DEPT_DOCS_DIR = Path(r"d:\2026\Stratos Enterprise\data\department_docs")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL = "llama-3.1-8b-instant"

client = Groq(api_key=GROQ_API_KEY)

# Load all valid employees by department
dept_employees = {}
for f in ROSTER_DIR.glob("*.json"):
    data = json.load(open(f, encoding="utf-8"))
    if data:
        dept = data[0]["department"]
        dept_employees[dept] = data

DEPT_CODE_MAP = {
    "Engineering": "ENG", "Finance": "FIN", "HR": "HR",
    "Legal": "LEG", "Sales": "SAL"
}

# PART A: Public Sensitivity Documents
public_docs = [
    {"dept": "HR", "type": "Employee Handbook", "sens": "Public", "code": "HND"},
    {"dept": "Engineering", "type": "Code Review Guidelines", "sens": "Public", "code": "CRG"},
    {"dept": "Finance", "type": "Public Finance FAQ", "sens": "Public", "code": "FAQ"},
    {"dept": "Legal", "type": "General Compliance Overview", "sens": "Public", "code": "GCO"},
    {"dept": "Sales", "type": "Sales Team Onboarding Guide", "sens": "Public", "code": "OBG"}
]

# PART B: Additional Variety Documents
variety_docs = [
    # HR
    {"dept": "HR", "type": "Leave Policy", "sens": "Internal", "code": "LVP"},
    {"dept": "HR", "type": "Appraisal Guidelines", "sens": "Confidential", "code": "APG"},
    {"dept": "HR", "type": "Diversity Report", "sens": "Internal", "code": "DVR"},
    # Finance
    {"dept": "Finance", "type": "Expense Reimbursement Policy", "sens": "Internal", "code": "ERP"},
    {"dept": "Finance", "type": "Internal Audit Report", "sens": "Restricted", "code": "IAR"},
    {"dept": "Finance", "type": "Vendor Invoice Sample", "sens": "Confidential", "code": "VIS"},
    # Legal
    {"dept": "Legal", "type": "Vendor NDA Template", "sens": "Restricted", "code": "NDA"},
    {"dept": "Legal", "type": "Data Privacy Compliance Policy", "sens": "Internal", "code": "DPP"},
    {"dept": "Legal", "type": "Employment Agreement Template", "sens": "Confidential", "code": "EAT"},
    # Engineering
    {"dept": "Engineering", "type": "System Architecture Document", "sens": "Internal", "code": "SAD"},
    {"dept": "Engineering", "type": "Production Incident Report", "sens": "Confidential", "code": "PIR"},
    {"dept": "Engineering", "type": "API Documentation", "sens": "Internal", "code": "API"},
    # Sales
    {"dept": "Sales", "type": "Pricing Sheet", "sens": "Confidential", "code": "PRS"},
    {"dept": "Sales", "type": "Sales Playbook", "sens": "Internal", "code": "SPB"},
    {"dept": "Sales", "type": "Client Proposal Template", "sens": "Internal", "code": "CPT"}
]

all_new_docs = public_docs + variety_docs

def generate_doc_content(doc, author_name):
    prompt = f"""Write a realistic Stratos Enterprises internal document for the following:
Department: {doc['dept']}
Document Type: {doc['type']}
Sensitivity Level: {doc['sens']}
Author: {author_name}

The document should be detailed, realistic, and contain between 400 to 600 words.
Include specific project names (e.g. Project Helios, CloudEdge 3.0), specific policy clauses, or numerical figures where relevant to Stratos Enterprises (a SaaS and cloud services company with HQ in Bangalore).
Do NOT use generic placeholder text.

Output ONLY the document body content. Do not include any title, markdown headers, or metadata. Just start with the text."""

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
                time.sleep(10)
            else:
                raise e

# Create files
for idx, doc in enumerate(all_new_docs):
    dept = doc["dept"]
    dept_code = DEPT_CODE_MAP[dept]
    
    # Pick a random or senior employee from that dept roster as author
    emps = dept_employees[dept]
    # Filter for managers/directors if possible, else pick first
    seniors = [e for e in emps if e["role_level"] in ["Director", "Manager"]]
    author = seniors[idx % len(seniors)] if seniors else emps[0]
    author_name = f"{author['full_name']}, {author['designation']}"
    
    doc_id = f"STR-{dept_code}-{doc['code']}-2025-001"
    
    print(f"[{idx+1}/20] Generating {doc['type']} for {dept} by {author_name}")
    
    body = generate_doc_content(doc, author_name)
    
    # Format with explicit ---METADATA--- tag
    header = (
        "---METADATA---\n"
        f"Document_ID: {doc_id}\n"
        f"Department: {dept}\n"
        f"Document_Type: {doc['type']}\n"
        f"Sensitivity_Level: {doc['sens']}\n"
        f"Created_Date: 2025-08-15\n"
        f"Author: {author_name}\n"
        "---END METADATA---\n\n"
    )
    
    filename = f"{doc_id}.txt"
    filepath = DEPT_DOCS_DIR / filename
    filepath.write_text(header + body, encoding="utf-8")
    print(f"  Saved {filename}")
    time.sleep(2)

print("\nDone generating 20 new department documents.")
