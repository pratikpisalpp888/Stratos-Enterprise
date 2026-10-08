import json
import time
import logging
from typing import Dict, Any
from groq import Groq
from app.config.settings import settings
from app.rbac.user_context import load_user_context, UserContext
from app.retrieval.query_router import classify_query_intent
from app.generation.rag_chain import run_rag_pipeline
from app.agents.tools import TOOL_REGISTRY
from app.agents.permission_gate import check_tool_permission

logger = logging.getLogger("app.agents.agent_orchestrator")

_groq_client = None

def _get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
    return _groq_client

EXTRACTION_SYSTEM_PROMPT = """You are an agentic tool extractor for an enterprise HR system.
Analyze the user's action query and extract the appropriate tool call and its arguments in raw JSON.

AVAILABLE TOOLS & REQUIRED ARGUMENTS:
1. "check_leave_balance": Check leave balance.
   - Arguments: {"target_employee_id": string or null}
2. "apply_leave": Apply for personal leave.
   - Arguments: {"start_date": string (YYYY-MM-DD or text), "end_date": string, "reason": string}
3. "approve_leave": Approve or reject a leave request.
   - Arguments: {"request_id": string (e.g. "LR-1001"), "decision": "Approved" or "Rejected"}
4. "generate_department_report": Generate departmental summary report.
   - Arguments: {"department": string (e.g., "Engineering", "Finance", "HR", "Legal", "Sales")}
5. "update_employee_record": Update HR record attributes.
   - Arguments: {"target_employee_id": string, "field": string, "new_value": string}

OUTPUT FORMAT:
Output ONLY a raw JSON object: {"tool_name": "...", "tool_args": {...}}
Do NOT include markdown block formatting or extra commentary.
"""

def extract_tool_call(query: str) -> Dict[str, Any]:
    """
    Uses Groq LLM to extract tool name and arguments from natural language query.
    """
    client = _get_groq_client()
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": f"Action Query: {query}"}
            ],
            model=settings.GROQ_FAST_MODEL,
            temperature=0.0,
            max_tokens=150
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()
            
        data = json.loads(content)
        return data
    except Exception as e:
        logger.error(f"Tool call extraction failed for '{query}': {e}")
        return {"tool_name": "check_leave_balance", "tool_args": {}}

def run_agent_pipeline(query: str, employee_id: str) -> Dict[str, Any]:
    """
    Unified entry point for both Info Queries (RAG Pipeline) and Action Requests (Agent Pipeline).
    """
    start_time = time.time()
    logger.info(f"=== UNIFIED ENTRY POINT | User: {employee_id} | Query: '{query[:40]}' ===")

    # 1. Classify Intent
    intent_info = classify_query_intent(query)
    intent = intent_info.get("intent", "policy_or_general_info")

    if intent == "chit_chat":
        logger.info(f"Intent classified as 'chit_chat'. Bypassing RAG and Agent pipelines.")
        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "answer": "Hello! I am SentinelRAG, your enterprise AI assistant. I'm functioning perfectly. How can I help you with your HR records, company policies, or action requests today?",
            "pipeline_stage": "CHIT_CHAT_BYPASS",
            "sources": [],
            "intent_classification": intent_info,
            "guardrail_flags": [],
            "response_time_ms": round(elapsed_ms, 2)
        }

    # If NOT an action request, route to RAG Pipeline (Phase 7)
    if intent != "action_request":
        logger.info(f"Intent '{intent}' is not an action_request. Routing to RAG Pipeline...")
        return run_rag_pipeline(query, employee_id)

    logger.info(f"Intent classified as 'action_request'. Entering Agent Tool Execution Flow...")

    # 2. Resolve User Context
    try:
        user = load_user_context(employee_id)
    except ValueError as e:
        return {
            "answer": f"Error: User '{employee_id}' not found in employee roster.",
            "pipeline_stage": "USER_RESOLUTION_FAILED",
            "sources": [],
            "intent_classification": intent_info,
            "guardrail_flags": ["INVALID_EMPLOYEE_ID"],
            "response_time_ms": round((time.time() - start_time) * 1000, 2)
        }

    # 3. Extract Tool & Arguments via LLM
    extracted = extract_tool_call(query)
    tool_name = extracted.get("tool_name")
    tool_args = extracted.get("tool_args") or {}

    tool_def = TOOL_REGISTRY.get(tool_name)
    if not tool_def:
        elapsed_ms = (time.time() - start_time) * 1000
        return {
            "answer": f"I could not identify a valid action to perform for query: '{query}'.",
            "pipeline_stage": "INVALID_TOOL_EXTRACTION",
            "sources": [],
            "intent_classification": intent_info,
            "guardrail_flags": [],
            "response_time_ms": round(elapsed_ms, 2)
        }

    # 4. HARDCODED PERMISSION CHECK (Critical Security Gate)
    perm_check = check_tool_permission(user, tool_name, **tool_args)
    if not perm_check["allowed"]:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.warning(f"PERMISSION DENIED for {user.employee_id} on tool {tool_name}: {perm_check['reason']}")
        return {
            "answer": f"Permission Denied: {perm_check['reason']}",
            "pipeline_stage": "AGENT_PERMISSION_DENIED",
            "sources": [],
            "intent_classification": intent_info,
            "tool_call": {
                "tool_name": tool_name,
                "tool_args": tool_args,
                "allowed": False,
                "reason": perm_check["reason"]
            },
            "guardrail_flags": ["AGENT_PERMISSION_DENIED"],
            "response_time_ms": round(elapsed_ms, 2)
        }

    # 5. Execute Authorized Tool
    tool_func = tool_def["func"]
    try:
        tool_result = tool_func(user, **tool_args)
        elapsed_ms = (time.time() - start_time) * 1000
        
        # Format user response message
        if perm_check.get("transparency_note"):
            msg = f"{perm_check['transparency_note']}\n(Leave Request ID: {tool_result['leave_request']['request_id']})"
        elif tool_result.get("message"):
            msg = tool_result["message"]
        else:
            msg = f"Successfully executed tool '{tool_name}'."

        if tool_name == "check_leave_balance":
            msg = (
                f"Leave Balance for Employee {tool_result['employee_id']}:\n"
                f"- Paid Leave Remaining: {tool_result['paid_leave_remaining']} days\n"
                f"- Casual Leave Remaining: {tool_result['casual_leave_remaining']} days\n"
                f"- Sick Leave Remaining: {tool_result['sick_leave_remaining']} days\n"
                f"- Pending Leave Requests: {tool_result['pending_requests_count']}"
            )
        elif tool_name == "generate_department_report":
            msg = f"Departmental Report for {tool_result['department']}:\n{tool_result['summary']}"

        return {
            "answer": msg,
            "pipeline_stage": "AGENT_ACTION_SUCCESS",
            "sources": [],
            "intent_classification": intent_info,
            "tool_call": {
                "tool_name": tool_name,
                "tool_args": tool_args,
                "allowed": True,
                "result": tool_result
            },
            "guardrail_flags": [],
            "response_time_ms": round(elapsed_ms, 2)
        }

    except Exception as e:
        elapsed_ms = (time.time() - start_time) * 1000
        logger.error(f"Execution of tool {tool_name} failed: {e}")
        return {
            "answer": f"Action Execution Error: Failed to execute tool '{tool_name}': {e}",
            "pipeline_stage": "TOOL_EXECUTION_FAILED",
            "sources": [],
            "intent_classification": intent_info,
            "response_time_ms": round(elapsed_ms, 2)
        }
