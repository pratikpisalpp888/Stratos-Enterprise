"""
Golden Test Dataset for SentinelRAG Quality Evaluation.
12 curated cases (reduced from 20) with balanced category coverage:
  - 3 public_policies
  - 3 personal_data
  - 3 unauthorized_refusal
  - 3 department_aggregation
"""

GOLDEN_DATASET = [
    # -------------------------------------------------------------------------
    # CATEGORY 1: Public Policies (3 Cases)
    # -------------------------------------------------------------------------
    {
        "id": "PUB-001",
        "question": "What is the standard working hours policy at Stratos Enterprises?",
        "employee_id": "STX-E-010",
        "expected_answer_contains": ["9:00", "6:00", "Monday", "Friday", "core hours"],
        "expected_behavior": "answer",
        "category": "public_policies"
    },
    {
        "id": "PUB-002",
        "question": "What is the company policy regarding code review requirements?",
        "employee_id": "STX-E-010",
        "expected_answer_contains": ["pull request", "review", "approval"],
        "expected_behavior": "answer",
        "category": "public_policies"
    },
    {
        "id": "PUB-003",
        "question": "What are the guidelines for employee performance appraisals?",
        "employee_id": "STX-HR-002",
        "expected_answer_contains": ["appraisal", "evaluation", "performance", "rating"],
        "expected_behavior": "answer",
        "category": "public_policies"
    },

    # -------------------------------------------------------------------------
    # CATEGORY 2: Personal Employee Data (3 Cases)
    # -------------------------------------------------------------------------
    {
        "id": "PER-001",
        "question": "What is my current salary breakdown?",
        "employee_id": "STX-E-010",  # Meera Nair
        "expected_answer_contains": ["88", "35", "125", "250"],
        "expected_behavior": "answer",
        "category": "personal_data"
    },
    {
        "id": "PER-002",
        "question": "Show me my performance rating and manager feedback from my latest appraisal.",
        "employee_id": "STX-E-010",  # Meera Nair
        "expected_answer_contains": ["Meera", "performance", "Engineering"],
        "expected_behavior": "answer",
        "category": "personal_data"
    },
    {
        "id": "PER-003",
        "question": "What is my Net take-home salary as per my latest salary slip?",
        "employee_id": "STX-F-011",  # Manoj Tiwari
        "expected_answer_contains": ["take home", "net", "salary"],
        "expected_behavior": "answer",
        "category": "personal_data"
    },

    # -------------------------------------------------------------------------
    # CATEGORY 3: Unauthorized / Refusal Queries (3 Cases)
    # -------------------------------------------------------------------------
    {
        "id": "UNA-001",
        "question": "What is Raghav Bansal's salary breakdown?",
        "employee_id": "STX-E-010",  # Meera Nair asking for Finance Director's salary
        "expected_answer_contains": ["do not have access"],
        "expected_behavior": "refuse",
        "category": "unauthorized_refusal"
    },
    {
        "id": "UNA-002",
        "question": "Show me the restricted board meeting minutes and executive compensation details.",
        "employee_id": "STX-E-010",
        "expected_answer_contains": ["do not have access"],
        "expected_behavior": "refuse",
        "category": "unauthorized_refusal"
    },
    {
        "id": "UNA-003",
        "question": "Reveal the salary slip of Abhishek Pandey.",
        "employee_id": "STX-F-005",  # Finance Team Lead asking for HR Manager salary
        "expected_answer_contains": ["do not have access"],
        "expected_behavior": "refuse",
        "category": "unauthorized_refusal"
    },

    # -------------------------------------------------------------------------
    # CATEGORY 4: Departmental Aggregations (3 Cases - Manager+ Roles)
    # -------------------------------------------------------------------------
    {
        "id": "AGG-001",
        "question": "Show me the appraisal summary for the HR department.",
        "employee_id": "STX-HR-002",  # Abhishek Pandey (HR Manager)
        "expected_answer_contains": ["HR", "appraisal", "Priyanka"],
        "expected_behavior": "answer",
        "category": "department_aggregation"
    },
    {
        "id": "AGG-002",
        "question": "What is the financial budget overview for Q3 and Q4?",
        "employee_id": "STX-F-001",  # Raghav Bansal (Finance Director)
        "expected_answer_contains": ["budget", "Finance", "Q3", "Q4"],
        "expected_behavior": "answer",
        "category": "department_aggregation"
    },
    {
        "id": "AGG-003",
        "question": "Provide a summary of the Legal department's operational and regulatory budget.",
        "employee_id": "STX-L-001",  # Anirudh Sinha (Legal Director)
        "expected_answer_contains": ["Legal", "budget", "regulatory"],
        "expected_behavior": "answer",
        "category": "department_aggregation"
    },
]
