import logging
from typing import Dict, Any, Optional
from app.rbac.user_context import UserContext
from app.agents.mock_data_store import (
    create_leave_request,
    get_leave_requests,
    get_leave_request_by_id,
    update_leave_request_status
)
from app.retrieval.hybrid_retriever import hybrid_search
from app.generation.llm_generator import generate_answer

logger = logging.getLogger("app.agents.tools")

def check_leave_balance(user: UserContext, target_employee_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Checks leave balance for user or target_employee_id (rule: SELF_OR_MANAGER).
    """
    tid = target_employee_id or user.employee_id
    existing_requests = get_leave_requests(tid)
    pending_count = sum(1 for r in existing_requests if r.get("status") == "Pending")
    approved_count = sum(1 for r in existing_requests if r.get("status") == "Approved")
    
    return {
        "status": "success",
        "employee_id": tid,
        "paid_leave_remaining": max(0, 18 - approved_count * 2),
        "casual_leave_remaining": 6,
        "sick_leave_remaining": 8,
        "pending_requests_count": pending_count,
        "approved_requests_count": approved_count
    }

def apply_leave(user: UserContext, start_date: str, end_date: str, reason: str) -> Dict[str, Any]:
    """
    Submits a leave request for user.employee_id (rule: SELF_ONLY).
    """
    req = create_leave_request(
        employee_id=user.employee_id,
        start_date=start_date,
        end_date=end_date,
        reason=reason
    )
    return {
        "status": "success",
        "message": f"Leave request {req['request_id']} submitted successfully from {start_date} to {end_date}.",
        "leave_request": req
    }

def approve_leave(user: UserContext, request_id: str, decision: str) -> Dict[str, Any]:
    """
    Approves or rejects a leave request (rule: MUST_BE_DIRECT_MANAGER).
    """
    status_val = "Approved" if "appr" in decision.lower() else "Rejected"
    updated_req = update_leave_request_status(
        request_id=request_id,
        status=status_val,
        approved_by=user.employee_id
    )
    if not updated_req:
        return {
            "status": "error",
            "message": f"Leave request '{request_id}' was not found."
        }
    return {
        "status": "success",
        "message": f"Leave request {request_id} has been marked as '{status_val}'.",
        "leave_request": updated_req
    }

def generate_department_report(user: UserContext, department: str) -> Dict[str, Any]:
    """
    Generates a departmental report summary using RBAC hybrid search and LLM (rule: MANAGER_PLUS_OWN_DEPT_OR_EXECUTIVE).
    """
    query = f"{department} department quarterly performance and budget summary"
    retrieval_res = hybrid_search(query, user, limit=5)
    chunks = [r["payload"] for r in retrieval_res["results"]]
    
    if chunks:
        summary_text = generate_answer(query, chunks, user)
    else:
        summary_text = f"Summary report generated for {department} department based on internal operations context."

    return {
        "status": "success",
        "department": department,
        "report_generated_by": user.full_name,
        "summary": summary_text,
        "sources_count": len(chunks)
    }

def update_employee_record(user: UserContext, target_employee_id: str, field: str, new_value: str) -> Dict[str, Any]:
    """
    Simulates updating an employee's HR record (rule: HR_ADMIN_ONLY).
    """
    return {
        "status": "simulated_success",
        "message": f"Simulated update of field '{field}' to '{new_value}' for employee {target_employee_id}.",
        "target_employee_id": target_employee_id,
        "field": field,
        "new_value": new_value,
        "updated_by": user.employee_id
    }

def send_enterprise_email(
    user: UserContext,
    recipient_query: str,
    message_instruction: str,
    subject_hint: Optional[str] = None
) -> Dict[str, Any]:
    """
    Sends an enterprise email via Stratos Gmail MCP Client with autonomous corporate drafting.
    (rule: MANAGER_OR_HR_EMAIL_DISPATCH).
    """
    from app.mcp.client import stratos_mcp_client
    return stratos_mcp_client.execute_send_email(
        sender=user,
        recipient_query=recipient_query,
        message_instruction=message_instruction,
        subject_hint=subject_hint
    )

# Registry mapping tool names to definitions and permission rule keys
TOOL_REGISTRY = {
    "check_leave_balance": {
        "name": "check_leave_balance",
        "description": "Check remaining leave balance for yourself or a team member.",
        "func": check_leave_balance,
        "permission_rule": "SELF_OR_MANAGER"
    },
    "apply_leave": {
        "name": "apply_leave",
        "description": "Submit a leave application for yourself.",
        "func": apply_leave,
        "permission_rule": "SELF_ONLY"
    },
    "approve_leave": {
        "name": "approve_leave",
        "description": "Approve or reject a pending leave request submitted by a direct report.",
        "func": approve_leave,
        "permission_rule": "MUST_BE_DIRECT_MANAGER"
    },
    "generate_department_report": {
        "name": "generate_department_report",
        "description": "Generate a departmental operational/budget summary report.",
        "func": generate_department_report,
        "permission_rule": "MANAGER_PLUS_OWN_DEPT_OR_EXECUTIVE"
    },
    "update_employee_record": {
        "name": "update_employee_record",
        "description": "Update an employee's HR record attributes.",
        "func": update_employee_record,
        "permission_rule": "HR_ADMIN_ONLY"
    },
    "send_enterprise_email": {
        "name": "send_enterprise_email",
        "description": "Send an official enterprise email to an employee or team member via Gmail MCP Client.",
        "func": send_enterprise_email,
        "permission_rule": "MANAGER_OR_HR_EMAIL_DISPATCH"
    }
}

