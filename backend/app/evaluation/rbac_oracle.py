"""
Independent Ground-Truth RBAC Oracle.
Re-implements the 6 access control rules in clean, standalone Python logic
WITHOUT importing backend/app/rbac/access_control.py to prevent circular testing.
"""

from typing import Dict, Any
from app.rbac.user_context import UserContext

def expected_access(user: UserContext, chunk_payload: Dict[str, Any]) -> bool:
    """
    Independent ground-truth access oracle.
    Returns True if user is authorized to read chunk_payload under enterprise policy, False otherwise.
    """
    min_clearance = chunk_payload.get("min_clearance_level", 0)
    dept = chunk_payload.get("department")
    owner_id = chunk_payload.get("owner_employee_id")
    manager_id = chunk_payload.get("manager_id")
    restricted_owner = chunk_payload.get("restricted_to_owner", False)
    access_roles = chunk_payload.get("access_roles") or []

    # Rule 1: Public Documents (min_clearance == 0 and not owner restricted)
    if min_clearance == 0 and not restricted_owner:
        return True

    # Rule 4: Self-Ownership (Always grants access to own docs)
    if owner_id and owner_id == user.employee_id:
        return True

    # Rule 5: Direct Manager Access (Manager can access direct reports' personal docs)
    if manager_id and manager_id == user.employee_id:
        return True

    # Rule 6: Special Admin Roles
    # HR-Admin has domain authority over Appraisals, Leave Records, and HR documents
    doc_type = chunk_payload.get("document_type") or ""
    if user.is_hr_admin:
        if "HR-Admin" in access_roles or doc_type in ["Appraisal Record", "Appraisal Guidelines", "Leave History Record", "Employee Handbook"]:
            return True

    # Finance-Admin has domain authority over Salary Slips, Financial Audits, and Budget documents
    if user.is_finance_admin:
        if "Finance-Admin" in access_roles or doc_type in ["Salary Slip", "Public Finance FAQ", "Quarterly Budget Report"]:
            return True

    # If document is strictly restricted to owner and caller is not owner/manager/admin
    if restricted_owner:
        return False

    # Rule 3: Cross-Department Executive Access (Level 3 Directors & C-Level)
    if user.clearance_level >= 3 and min_clearance <= user.clearance_level:
        return True

    # Rule 2: Department + Clearance Match
    if dept and dept == user.department and user.clearance_level >= min_clearance:
        return True

    return False
