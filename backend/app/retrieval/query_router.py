import re
import json
import time
import logging
from groq import Groq
from app.config.settings import settings

logger = logging.getLogger("app.retrieval.query_router")

# Cache Groq client
_groq_client = None

def _get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
    return _groq_client

SYSTEM_PROMPT = """You are a query intent classifier for an enterprise RAG system.
Classify the user's search query into EXACTLY ONE of these categories:
1. "personal_record_lookup": Searching for individual employee documents, records, salary, performance ratings, appraisals, or specific personal records (e.g., "my salary", "Manoj's leave balance", "employee appraisal rating", "Deepak appraisal").
2. "policy_or_general_info": Searching for company-wide policies, guidelines, handbooks, FAQs, or general procedures (e.g., "what is the leave policy", "appraisal guidelines", "code review guidelines").
3. "aggregate_or_report": Searching for department/company reports, budget overviews, financial audits, or team summaries (e.g., "quarterly budget report", "Q3 financial summary", "vendor NDA template").
4. "action_request": Requesting an action or tool execution to be performed (e.g., "apply for leave", "approve leave", "update employee record", "generate report", "create report", "send email", "email to", "send mail", "draft email").
5. "chit_chat": Basic conversational pleasantries or greetings (e.g., "hi", "hello", "how are you", "who are you", "good morning", "thank you").

Output ONLY a raw JSON object with keys "intent" and "confidence" (values: "high", "medium", "low").
Do NOT include markdown formatting or extra text. Example:
{"intent": "personal_record_lookup", "confidence": "high"}
"""

VALID_INTENTS = {"personal_record_lookup", "policy_or_general_info", "aggregate_or_report", "action_request", "chit_chat"}

def classify_query_intent(query: str) -> dict:
    """
    Classifies a search query into an intent category using Groq's fast LLM model.
    Falls back to 'policy_or_general_info' if parsing or API fails.
    Includes exponential backoff (max 3 retries, max 20s wait) for rate limits.
    """
    client = _get_groq_client()
    for attempt in range(1, 6):
        try:
            response = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Query: {query}"}
                ],
                model=settings.GROQ_FAST_MODEL,
                temperature=0.0,
                max_tokens=150
            )
            content = response.choices[0].message.content.strip()
            match = re.search(r"\{.*\}|\[.*\]", content, re.DOTALL)
            if match:
                content = match.group(0)
            else:
                content = content.strip()

            data = json.loads(content)
            intent = data.get("intent", "policy_or_general_info")
            confidence = data.get("confidence", "medium")

            if intent not in VALID_INTENTS:
                intent = "policy_or_general_info"

            logger.info(f"Query: '{query[:40]}' classified as intent='{intent}' (confidence={confidence})")
            return {"intent": intent, "confidence": confidence}

        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = any(sig in err_str for sig in ["rate limit", "429", "quota", "tokens per"])
            logger.warning(f"Groq query classification attempt {attempt} failed for '{query[:40]}': {e}")
            
            if is_rate_limit:
                wait_time = 5 * (2 ** (attempt - 1))
                logger.info(f"Rate limit hit. Pausing for {wait_time}s before retrying...")
                time.sleep(wait_time)
                continue
            
            if attempt == 5 or not is_rate_limit:
                logger.info(f"Groq failed persistently. Falling back immediately to local Ollama ({settings.OLLAMA_MODEL})...")
                try:
                    from ollama import Client
                    ollama_client = Client(host=settings.OLLAMA_BASE_URL, timeout=60)
                    response = ollama_client.chat(
                        model=settings.OLLAMA_MODEL,
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": f"Query: {query}"}
                        ],
                        format="json",
                        options={"temperature": 0.0, "num_predict": 100}
                    )
                    content = response["message"]["content"].strip()
                    match = re.search(r"\{.*\}|\[.*\]", content, re.DOTALL)
                    if match:
                        content = match.group(0)
                    data = json.loads(content)
                    intent = data.get("intent", "policy_or_general_info")
                    confidence = data.get("confidence", "medium")
                    if intent not in VALID_INTENTS:
                        intent = "policy_or_general_info"
                    logger.info(f"Ollama query classification fallback successful: intent='{intent}'")
                    return {"intent": intent, "confidence": confidence}
                except Exception as ollama_err:
                    logger.error(f"Ollama query classification fallback failed: {ollama_err}")

            time.sleep(2)

    return {"intent": "policy_or_general_info", "confidence": "low"}
