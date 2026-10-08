import re
import json
import logging
from typing import List, Dict, Any
from groq import Groq
from app.config.settings import settings
from app.rbac.user_context import UserContext, _get_roster

logger = logging.getLogger("app.guardrails.output_guardrails")

_groq_client = None

def _get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
    return _groq_client

SYSTEM_GROUNDING_PROMPT = """You are a citation grounding verifier for an enterprise RAG system.
Verify if the claims made in the generated answer are grounded in (supported by) the provided source context.

Source Context:
{context}

Generated Answer:
{answer}

Output ONLY a JSON object: {"is_grounded": true/false, "confidence": "high/medium/low", "reasoning": "brief explanation"}
Do NOT include markdown formatting or extra text.
"""

def check_citation_grounding(generated_answer: str, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    NLI-style check to verify if the generated answer is grounded in retrieved context chunks.
    Valid refusal statements (e.g. 'I do not have access') are marked grounded.
    """
    answer_lower = generated_answer.lower()
    refusal_phrases = [
        "do not have access",
        "don't have access",
        "does not contain",
        "do not contain",
        "no information",
        "not mentioned",
        "cannot provide"
    ]
    if any(phrase in answer_lower for phrase in refusal_phrases):
        return {
            "is_grounded": True,
            "confidence": "high",
            "reasoning": "Valid refusal statement for ungrounded/absent information in retrieved context."
        }

    if not retrieved_chunks:
        return {
            "is_grounded": False,
            "confidence": "high",
            "reasoning": "No source context chunks were provided for grounding check."
        }

    # Concatenate chunk contents for context
    context_text = "\n---\n".join([
        c.get("content") or c.get("payload", {}).get("content", "")
        for c in retrieved_chunks
    ])

    try:
        client = _get_groq_client()
        prompt = SYSTEM_GROUNDING_PROMPT.replace("{context}", context_text[:3000]).replace("{answer}", generated_answer)
        
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=settings.GROQ_FAST_MODEL,
            temperature=0.0,
            max_tokens=100
        )
        content = response.choices[0].message.content.strip()
        
        # Extract json pattern using regex
        match = re.search(r"\{.*\}", content, re.DOTALL)
        if match:
            json_str = match.group(0)
        else:
            json_str = content

        raw_data = json.loads(json_str)
        # Normalize dictionary keys by stripping literal quotes if any exist
        data = {str(k).strip().strip('"').strip("'"): v for k, v in raw_data.items()}
        
        is_grounded = bool(data.get("is_grounded", False))
        conf = str(data.get("confidence", "medium"))
        reasoning = str(data.get("reasoning", ""))
        
        return {
            "is_grounded": is_grounded,
            "confidence": conf,
            "reasoning": reasoning
        }
    except Exception as e:
        logger.warning(f"Citation grounding check failed: {e}")
        return {"is_grounded": True, "confidence": "low", "reasoning": f"Grounding check exception: {e}"}


def detect_rbac_leak_in_output(generated_answer: str, user: UserContext, retrieved_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Verifies that the generated answer does NOT mention employees whose records
    were NOT present in the RBAC-filtered retrieved_chunks context.
    """
    roster = _get_roster()
    
    # Collect all authorized names/IDs from user context and retrieved chunks metadata/content
    authorized_names = {user.full_name.lower()}
    authorized_ids = {user.employee_id.lower()}
    
    for chunk in retrieved_chunks:
        payload = chunk.get("payload") or chunk
        content_text = (payload.get("content") or "").lower()
        owner_name = payload.get("owner_name")
        owner_id = payload.get("owner_employee_id")
        author = payload.get("author")
        
        if owner_name:
            authorized_names.add(owner_name.lower())
        if owner_id:
            authorized_ids.add(owner_id.lower())
        if author:
            authorized_names.add(author.split(",")[0].lower())

        # Also authorize any employee name/ID explicitly appearing within the retrieved chunk text
        for emp_id, emp_data in roster.items():
            emp_name = emp_data["full_name"].lower()
            if emp_name in content_text or emp_id.lower() in content_text:
                authorized_names.add(emp_name)
                authorized_ids.add(emp_id.lower())

    unauthorized_entities = []
    
    # Scan generated answer for mentions of roster employees
    for emp_id, emp_data in roster.items():
        name = emp_data["full_name"]
        
        # Skip if this employee is authorized in the context or is the querying user
        if name.lower() in authorized_names or emp_id.lower() in authorized_ids:
            continue
            
        # Check if unauthorized employee name or ID appears in generated answer
        if name.lower() in generated_answer.lower() or emp_id.lower() in generated_answer.lower():
            unauthorized_entities.append(f"{name} ({emp_id})")

    leak_detected = len(unauthorized_entities) > 0
    if leak_detected:
        logger.warning(f"Output RBAC leak detected! Unauthorized entities mentioned: {unauthorized_entities}")

    return {
        "leak_detected": leak_detected,
        "unauthorized_entities_mentioned": unauthorized_entities
    }


def redact_sensitive_fields(text: str, user: UserContext) -> str:
    """
    Masks highly sensitive identity & financial patterns (PAN, Aadhaar, Bank numbers)
    in generated text as defense-in-depth.
    """
    redacted = text
    
    # Mask PAN Card numbers: ABCDE1234F -> ABCDE****F
    redacted = re.sub(
        r"\b([A-Z]{5})[0-9]{4}([A-Z]{1})\b",
        r"\1****\2",
        redacted
    )
    
    # Mask Aadhaar numbers: 1234 5678 9012 -> XXXX-XXXX-9012
    redacted = re.sub(
        r"\b[2-9]{1}[0-9]{3}\s?[0-9]{4}\s?([0-9]{4})\b",
        r"XXXX-XXXX-\1",
        redacted
    )
    
    # Mask Bank/Card numbers: 1234567890123456 -> XXXX-XXXX-3456
    redacted = re.sub(
        r"\b\d{8,12}(\d{4})\b",
        r"XXXX-XXXX-\1",
        redacted
    )
    
    return redacted


def run_output_guardrails(generated_answer: str, retrieved_chunks: List[Dict[str, Any]], user: UserContext) -> Dict[str, Any]:
    """
    Orchestrates output safety checks: grounding, RBAC leak detection, and redaction.
    Blocks/replaces answer if leak or hallucination is detected.
    """
    grounding_res = check_citation_grounding(generated_answer, retrieved_chunks)
    leak_res = detect_rbac_leak_in_output(generated_answer, user, retrieved_chunks)
    
    passed = True
    flags = []
    block_reason = None
    final_answer = redact_sensitive_fields(generated_answer, user)

    if leak_res["leak_detected"]:
        passed = False
        flags.append("OUTPUT_RBAC_LEAK_DETECTED")
        block_reason = f"Response blocked: Contains details of unauthorized employee(s): {', '.join(leak_res['unauthorized_entities_mentioned'])}."
        final_answer = "[SECURITY BLOCK] The generated response was blocked because it referenced employee details outside your authorized clearance."

    elif not grounding_res["is_grounded"] and grounding_res["confidence"] == "high":
        passed = False
        flags.append("UNGROUNDED_HALLUCINATION_DETECTED")
        block_reason = f"Response blocked: Unverified claims or hallucination detected. ({grounding_res.get('reasoning')})"
        final_answer = "[SAFETY BLOCK] The response could not be verified against available enterprise documents."

    return {
        "passed": passed,
        "final_answer": final_answer,
        "flags": flags,
        "block_reason": block_reason,
        "grounding_check": grounding_res,
        "leak_check": leak_res
    }
