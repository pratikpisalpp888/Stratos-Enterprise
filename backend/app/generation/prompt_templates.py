import logging
from typing import List, Dict, Any
from app.rbac.user_context import UserContext

logger = logging.getLogger("app.generation.prompt_templates")

SYSTEM_PROMPT_TEMPLATE = """You are SentinelAI, an enterprise AI assistant for Stratos Enterprises.
You provide accurate, professional, and strictly grounded responses based ONLY on the authorized context chunks provided below.

USER CONTEXT:
- Name: {full_name}
- Employee ID: {employee_id}
- Designation: {designation}
- Department: {department}
- Role Level: {role_level}
- Clearance Level: {clearance_level}

STRICT INSTRUCTIONS:
1. ANSWER ONLY USING THE PROVIDED CONTEXT: Base your answer strictly on the information in the retrieved context chunks below. Do NOT invent, assume, or extrapolate facts.
2. MISSING OR RESTRICTED INFORMATION: If the context does not contain sufficient information to answer the query, reply clearly: "I do not have access to that information in the available context."
3. PRIVACY & OTHER EMPLOYEES: Do NOT mention, guess, or speculate about details of other employees unless their information is explicitly contained in the provided context chunks.
4. NATURAL TONE (CRITICAL): Do NOT mention the words "chunks", "provided context", "retrieved documents", or "based on the text". Respond naturally as if you inherently know the answer. The user should not know you are reading from chunks.
5. FORMATTING: Be concise, clear, and professional. Use markdown bullet points for structured data (e.g. salary components, policy clauses, rating summaries).

--- RETRIEVED CONTEXT CHUNKS ---
{context_text}
--- END RETRIEVED CONTEXT CHUNKS ---

USER QUERY: {query}

ANSWER:"""

def build_generation_prompt(query: str, retrieved_chunks: List[Dict[str, Any]], user: UserContext) -> str:
    """
    Formats the final prompt for the LLM generator, injecting user context
    and formatting retrieved context chunks clearly.
    """
    context_blocks = []
    for idx, chunk in enumerate(retrieved_chunks, start=1):
        payload = chunk.get("payload") or chunk
        doc_type = payload.get("document_type", "Document")
        dept = payload.get("department", "Company-wide")
        owner = payload.get("owner_name")
        owner_str = f" | Owner: {owner}" if owner else ""
        content = payload.get("content", "").strip()
        
        block = f"--- CHUNK {idx} [{doc_type} | Dept: {dept}{owner_str}] ---\n{content}"
        context_blocks.append(block)

    formatted_context = "\n\n".join(context_blocks) if context_blocks else "No relevant context retrieved."

    prompt = SYSTEM_PROMPT_TEMPLATE.format(
        full_name=user.full_name,
        employee_id=user.employee_id,
        designation=user.designation,
        department=user.department,
        role_level=user.role_level,
        clearance_level=user.clearance_level,
        context_text=formatted_context,
        query=query
    )

    return prompt
