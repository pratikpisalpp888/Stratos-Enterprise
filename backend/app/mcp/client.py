import logging
from typing import Dict, Any, Optional
from app.rbac.user_context import UserContext, _get_roster
from app.mcp.gmail_mcp_server import gmail_mcp_server
from app.mcp.email_drafter import draft_professional_email

logger = logging.getLogger("app.mcp.client")

class StratosMCPClient:
    """
    Model Context Protocol (MCP) Client for Stratos Enterprise.
    Connects to internal and external MCP servers and bridges them into agent execution.
    """

    def __init__(self):
        self.gmail_server = gmail_mcp_server

    def resolve_recipient(self, query_or_name: str) -> Optional[Dict[str, Any]]:
        """
        Resolves a name, employee_id, or email query against the verified employee roster.
        """
        roster = _get_roster()
        clean_q = query_or_name.strip().lower()

        # 1. Direct email match
        if "@" in clean_q:
            for emp in roster.values():
                if emp.get("email", "").lower() == clean_q:
                    return emp
            return {"full_name": clean_q.split("@")[0], "email": clean_q, "designation": "External / Contact"}

        # 2. Direct ID match
        if clean_q.upper() in roster:
            return roster[clean_q.upper()]

        # 3. First name / Last name substring search
        for emp in roster.values():
            fn = emp.get("full_name", "").lower()
            if clean_q in fn or fn in clean_q:
                return emp

        # 4. Keyword fuzzy check (e.g. 'bharat', 'pratik', 'manoj')
        tokens = clean_q.split()
        for emp in roster.values():
            fn = emp.get("full_name", "").lower()
            if any(t in fn for t in tokens if len(t) >= 3):
                return emp

        return None

    def execute_send_email(
        self,
        sender: UserContext,
        recipient_query: str,
        message_instruction: str,
        subject_hint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        MCP Tool execution pipeline:
        1. Resolve recipient -> Target Email
        2. LLM Drafts polished corporate email
        3. MCP Client calls Gmail MCP Server
        """
        recipient_info = self.resolve_recipient(recipient_query)
        if not recipient_info:
            return {
                "status": "error",
                "message": f"Could not find employee matching '{recipient_query}' in employee roster. Please provide a valid employee name or email address."
            }

        recipient_name = recipient_info.get("full_name", recipient_query)
        recipient_email = recipient_info.get("email")
        recipient_title = recipient_info.get("designation", "Team Member")

        if not recipient_email:
            return {
                "status": "error",
                "message": f"Employee '{recipient_name}' does not have an active email address registered in the system."
            }

        # Step 2: LLM Autonomous Corporate Drafting
        logger.info(f"Drafting corporate email from {sender.full_name} to {recipient_name}...")
        draft = draft_professional_email(
            instruction=message_instruction,
            sender_name=sender.full_name,
            sender_role=sender.designation or sender.role_level,
            sender_department=sender.department,
            recipient_name=recipient_name,
            recipient_title=recipient_title
        )

        subject = subject_hint if subject_hint else draft["subject"]
        body = draft["body"]

        # Step 3: Call Gmail MCP Server
        logger.info(f"MCP Client invoking send_email tool for recipient: {recipient_email}")
        mcp_result = self.gmail_server.call_tool(
            tool_name="send_email",
            arguments={
                "to_email": recipient_email,
                "subject": subject,
                "body": body
            }
        )

        return {
            "status": "success",
            "message": f"Email successfully dispatched to {recipient_name} ({recipient_email}).",
            "recipient_name": recipient_name,
            "recipient_email": recipient_email,
            "recipient_designation": recipient_title,
            "subject": subject,
            "body_preview": body,
            "message_id": mcp_result.get("message_id"),
            "timestamp": mcp_result.get("timestamp")
        }

# Singleton client
stratos_mcp_client = StratosMCPClient()
