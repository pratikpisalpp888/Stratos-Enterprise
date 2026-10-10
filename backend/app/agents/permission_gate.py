import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from app.rbac.user_context import UserContext, _get_roster
from app.agents.tools import TOOL_REGISTRY
from app.agents.mock_data_store import get_leave_request_by_id

logger = logging.getLogger("app.agents.permission_gate")

DATA_DIR = Path(__file__).parent / "data"
AUDIT_FILE = DATA_DIR / "audit_log.json"

def _log_audit_entry(user: UserContext, tool_name: str, tool_args: dict, allowed: bool, reason: str) -> None:
    """
    Logs an immutable security audit trail of every tool execution attempt to JSON.
    """
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        entries = []
        if AUDIT_FILE.exists():
            with open(AUDIT_FILE, "r", encoding="utf-8") as f:
                entries = json.load(f)
                
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user_id": user.employee_id,
            "user_name": user.full_name,
            "user_role": user.role_level,
            "user_department": user.department,
            "tool_name": tool_name,
            "tool_args": tool_args,
            "allowed": allowed,
            "decision_reason": reason
        }
        entries.append(entry)
        with open(AUDIT_FILE, "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to log audit entry: {e}")


def check_tool_permission(user: UserContext, tool_name: str, **tool_args) -> Dict[str, Any]:
    """
    Independent Hardcoded Permission Gate.
    Evaluates permission rules strictly in Python logic using ground-truth UserContext.
    Rejects any prompt manipulation attempts or unauthorized tool invocations.
    """
    tool_info = TOOL_REGISTRY.get(tool_name)
    if not tool_info:
        reason = f"Security Error: Tool '{tool_name}' is not registered in security policy."
        _log_audit_entry(user, tool_name, tool_args, False, reason)
        return {"allowed": False, "reason": reason}

    rule_type = tool_info["permission_rule"]
    roster = _get_roster()
    allowed = False
    reason = ""

    # Rule 1: SELF_ONLY
    transparency_note = None
    if rule_type == "SELF_ONLY":
        target_id = tool_args.get("target_employee_id") or tool_args.get("requested_for")
        target_name = None
        
        # Scan tool args and user context for mentions of other roster employees
        for emp_id, emp_data in roster.items():
            if emp_id != user.employee_id:
                if emp_data["full_name"].lower() in str(tool_args).lower() or emp_id.lower() in str(tool_args).lower():
                    target_name = emp_data["full_name"]
                    break

        allowed = True
        if target_name or (target_id and target_id != user.employee_id):
            disp_target = target_name or target_id
            transparency_note = (
                f"I can only apply leave requests for yourself. I've created this leave request "
                f"for you ({user.full_name}), not for {disp_target}, as you don't have permission "
                f"to apply leave on behalf of other employees."
            )
            reason = f"Permission granted for caller ({user.employee_id}); requested target {disp_target} overridden to caller."
        else:
            reason = f"Permission granted for self-action by {user.employee_id}."

    # Rule 2: SELF_OR_MANAGER
    elif rule_type == "SELF_OR_MANAGER":
        target_id = tool_args.get("target_employee_id") or user.employee_id
        if target_id == user.employee_id:
            allowed = True
            reason = f"Permission granted: Checking own records ({user.employee_id})."
        else:
            target_emp = roster.get(target_id)
            if target_emp and target_emp.get("manager_id") == user.employee_id:
                allowed = True
                reason = f"Permission granted: User {user.employee_id} is direct manager of target {target_id}."
            else:
                allowed = False
                reason = f"Access Denied: User {user.employee_id} is not the direct manager of employee {target_id}."

    # Rule 3: MUST_BE_DIRECT_MANAGER
    elif rule_type == "MUST_BE_DIRECT_MANAGER":
        req_id = tool_args.get("request_id")
        if not req_id:
            allowed = False
            reason = "Security Error: Missing request_id argument for leave approval."
        else:
            req = get_leave_request_by_id(req_id)
            if not req:
                allowed = False
                reason = f"Request Not Found: Leave request '{req_id}' does not exist."
            else:
                target_id = req.get("employee_id")
                target_emp = roster.get(target_id)
                actual_mgr = target_emp.get("manager_id") if target_emp else None
                if actual_mgr == user.employee_id:
                    allowed = True
                    reason = f"Permission granted: {user.employee_id} is the verified manager of request {req_id} (employee: {target_id})."
                else:
                    allowed = False
                    reason = f"Access Denied: You ({user.employee_id}) are not authorized to approve leave for {target_id} (Manager: {actual_mgr})."

    # Rule 4: MANAGER_PLUS_OWN_DEPT_OR_EXECUTIVE
    elif rule_type == "MANAGER_PLUS_OWN_DEPT_OR_EXECUTIVE":
        dept = tool_args.get("department")
        if user.clearance_level >= 3:
            allowed = True
            reason = f"Permission granted: Executive clearance (level {user.clearance_level}) allows cross-department report generation."
        elif user.role_level in ["Manager", "Director", "C-Level"] and user.department == dept:
            allowed = True
            reason = f"Permission granted: Manager level in own department ({dept})."
        else:
            allowed = False
            reason = f"Access Denied: Department reports for {dept} require Manager+ role in {dept} or Executive clearance (Your role: {user.role_level} in {user.department})."

    # Rule 5: HR_ADMIN_ONLY
    elif rule_type == "HR_ADMIN_ONLY":
        if user.is_hr_admin:
            allowed = True
            reason = f"Permission granted: Verified HR-Admin privileges for user {user.employee_id}."
        else:
            allowed = False
            reason = f"Access Denied: HR record updates require HR-Admin privileges (Your department: {user.department}, Role: {user.role_level})."

    # Rule 6: MANAGER_OR_HR_EMAIL_DISPATCH
    elif rule_type == "MANAGER_OR_HR_EMAIL_DISPATCH":
        if user.role_level in ["Manager", "Director", "C-Level"] or user.clearance_level >= 2 or user.is_hr_admin:
            allowed = True
            reason = f"Permission granted: Manager/Executive role ({user.role_level} in {user.department}) allows enterprise email dispatch."
        else:
            allowed = False
            reason = f"Access Denied: Enterprise email dispatch requires Manager+ role or HR-Admin privileges (Your role: {user.role_level} in {user.department})."

    else:
        allowed = False
        reason = f"Security Error: Unknown permission rule '{rule_type}'."

    logger.info(f"Permission Check | Tool: {tool_name} | User: {user.employee_id} | Allowed: {allowed} | Reason: {reason}")
    _log_audit_entry(user, tool_name, tool_args, allowed, reason)
    
    return {"allowed": allowed, "reason": reason, "transparency_note": transparency_note}
