import json
import logging
from typing import Dict, Any, Optional
from groq import Groq
from app.config.settings import settings

logger = logging.getLogger("app.mcp.email_drafter")

_groq_client: Optional[Groq] = None

def _get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
    return _groq_client

DRAFTER_SYSTEM_PROMPT = """You are an Executive Enterprise Email Drafter for Stratos Enterprise.
Your mission is to convert casual or natural language manager instructions into crisp, professional, and courteous corporate emails.

GUIDELINES:
1. SUBJECT LINE: Short, executive, clear (e.g., "Sprint Retrospective - Tomorrow at 10:00 AM", "Project Milestone Review").
2. GREETING: Polite and personalized (e.g., "Hi Bharat,", "Dear Team,").
3. BODY:
   - Clear context and intent based directly on the user's instructions.
   - Use concise bullet points for action items or deadlines if appropriate.
   - Maintain a constructive, professional corporate tone.
4. SIGN-OFF: Professional closing matching the sender's title (e.g., "Best regards,\nPratik Pisal\nEngineering Manager | Stratos Enterprise").
5. OUTPUT FORMAT:
   Return ONLY a valid JSON object with EXACTLY two keys:
   {
     "subject": "Clear Subject Line",
     "body": "Complete plain text email body including greeting and sign-off."
   }
Do NOT include markdown fences (```json), commentary, or extra keys.
"""

def draft_professional_email(
    instruction: str,
    sender_name: str,
    sender_role: str,
    sender_department: str,
    recipient_name: str,
    recipient_title: Optional[str] = None
) -> Dict[str, str]:
    """
    Transforms natural language instruction into a professional corporate email draft.
    """
    client = _get_groq_client()
    user_prompt = f"""
SENDER CONTEXT:
- Name: {sender_name}
- Role/Title: {sender_role}
- Department: {sender_department}

RECIPIENT CONTEXT:
- Name: {recipient_name}
- Title: {recipient_title or 'Team Member'}

MANAGER INSTRUCTION / CONTEXT:
"{instruction}"

Please craft a professional corporate email draft based on this instruction.
"""

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": DRAFTER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            model=settings.GROQ_FAST_MODEL,
            temperature=0.2,
            max_tokens=400
        )
        content = response.choices[0].message.content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        data = json.loads(content)
        subject = data.get("subject", "Stratos Enterprise Communication")
        body = data.get("body", instruction)
        return {
            "subject": subject,
            "body": body
        }
    except Exception as e:
        logger.error(f"LLM email drafting failed: {e}. Falling back to default format.")
        fallback_subject = f"Notice from {sender_name} ({sender_department})"
        fallback_body = (
            f"Hi {recipient_name},\n\n"
            f"{instruction}\n\n"
            f"Best regards,\n"
            f"{sender_name}\n"
            f"{sender_role} | Stratos Enterprise"
        )
        return {
            "subject": fallback_subject,
            "body": fallback_body
        }
