import os
import uuid
import smtplib
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from app.config.settings import settings

logger = logging.getLogger("app.mcp.gmail_server")

class GmailMCPServer:
    """
    Model Context Protocol (MCP) Server for Gmail Integration.
    Exposes standard MCP tool definitions and handles secure SMTP TLS execution.
    """

    def __init__(self):
        self.host = "smtp.gmail.com"
        self.port = 587

    @property
    def sender_email(self) -> str:
        return settings.GMAIL_SENDER_EMAIL or "pratikpisalpp88@gmail.com"

    @property
    def app_password(self) -> str:
        raw_pw = settings.GMAIL_APP_PASSWORD or ""
        return raw_pw.replace(" ", "").strip()

    def list_tools(self) -> list[Dict[str, Any]]:
        """Standard MCP tools/list definition."""
        return [
            {
                "name": "send_email",
                "description": "Sends a real email through Google Mail SMTP with TLS encryption.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "to_email": {
                            "type": "string",
                            "description": "Recipient email address"
                        },
                        "subject": {
                            "type": "string",
                            "description": "Email subject line"
                        },
                        "body": {
                            "type": "string",
                            "description": "Plain text email body"
                        },
                        "html_body": {
                            "type": "string",
                            "description": "Optional styled HTML email body"
                        },
                        "cc": {
                            "type": "string",
                            "description": "Optional comma-separated CC email addresses"
                        }
                    },
                    "required": ["to_email", "subject", "body"]
                }
            },
            {
                "name": "preview_email",
                "description": "Generates a preview payload for an email without sending.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "to_email": {"type": "string"},
                        "subject": {"type": "string"},
                        "body": {"type": "string"}
                    },
                    "required": ["to_email", "subject", "body"]
                }
            }
        ]

    def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Standard MCP tools/call executor."""
        if tool_name == "send_email":
            return self._execute_send_email(
                to_email=arguments.get("to_email", ""),
                subject=arguments.get("subject", ""),
                body=arguments.get("body", ""),
                html_body=arguments.get("html_body"),
                cc=arguments.get("cc")
            )
        elif tool_name == "preview_email":
            return {
                "status": "preview_ready",
                "to_email": arguments.get("to_email"),
                "subject": arguments.get("subject"),
                "body": arguments.get("body"),
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise ValueError(f"Unknown MCP tool: '{tool_name}'")

    def _execute_send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None,
        cc: Optional[str] = None
    ) -> Dict[str, Any]:
        if not to_email or "@" not in to_email:
            raise ValueError(f"Invalid recipient email address: '{to_email}'")
        if not subject:
            raise ValueError("Email subject cannot be empty.")
        if not body:
            raise ValueError("Email body cannot be empty.")

        sender = self.sender_email
        pw = self.app_password

        if not pw:
            raise RuntimeError("GMAIL_APP_PASSWORD is not configured in backend/.env")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Stratos Enterprise <{sender}>"
        msg["To"] = to_email
        recipients = [to_email]

        if cc:
            msg["Cc"] = cc
            recipients.extend([c.strip() for c in cc.split(",") if c.strip()])

        # Attach plain text
        msg.attach(MIMEText(body, "plain", "utf-8"))

        # Attach rich HTML if provided
        if html_body:
            msg.attach(MIMEText(html_body, "html", "utf-8"))
        else:
            # Generate clean default corporate HTML
            clean_html = f"""
            <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 8px;">
                <div style="border-bottom: 2px solid #2563eb; padding-bottom: 12px; margin-bottom: 16px;">
                    <h2 style="color: #0f172a; margin: 0; font-size: 20px;">Stratos Enterprise Notice</h2>
                </div>
                <div style="color: #334155; font-size: 15px; line-height: 1.6; white-space: pre-line;">
                    {body}
                </div>
                <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 24px 0 12px 0;" />
                <p style="color: #94a3b8; font-size: 12px; margin: 0;">
                    This communication was dispatched automatically via Stratos Enterprise Agentic System.
                </p>
            </div>
            """
            msg.attach(MIMEText(clean_html, "html", "utf-8"))

        message_id = f"MSG-{uuid.uuid4().hex[:8].upper()}"

        try:
            logger.info(f"Connecting to {self.host}:{self.port} to dispatch email to {to_email}...")
            with smtplib.SMTP(self.host, self.port, timeout=15) as server:
                server.ehlo()
                server.starttls()
                server.login(sender, pw)
                server.sendmail(sender, recipients, msg.as_string())

            logger.info(f"Email successfully delivered to {to_email} (Ref: {message_id})")
            return {
                "status": "success",
                "message_id": message_id,
                "sender": sender,
                "recipient": to_email,
                "subject": subject,
                "timestamp": datetime.now().isoformat(),
                "delivered": True
            }
        except Exception as e:
            logger.error(f"Gmail SMTP dispatch failed: {e}")
            raise RuntimeError(f"Gmail SMTP dispatch error: {str(e)}")

# Singleton instance
gmail_mcp_server = GmailMCPServer()
