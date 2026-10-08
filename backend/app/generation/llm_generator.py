import time
import logging
from typing import List, Dict, Any
from groq import Groq
from app.config.settings import settings
from app.rbac.user_context import UserContext
from app.generation.prompt_templates import build_generation_prompt

logger = logging.getLogger("app.generation.llm_generator")

_groq_client = None

def _get_groq_client() -> Groq:
    global _groq_client
    if _groq_client is None:
        _groq_client = Groq(api_key=settings.GROQ_API_KEY)
    return _groq_client

def generate_answer(query: str, retrieved_chunks: List[Dict[str, Any]], user: UserContext) -> str:
    """
    Generates a role-aware, grounded response using Groq's main model (llama-3.3-70b-versatile).
    Includes retry logic for API resilience.
    """
    prompt = build_generation_prompt(query, retrieved_chunks, user)
    client = _get_groq_client()
    
    models_to_try = [settings.GROQ_MODEL, settings.GROQ_FAST_MODEL]
    for attempt in range(1, 6):
        model_name = models_to_try[0] if attempt <= 3 else models_to_try[1]
        try:
            logger.info(f"Generating LLM answer for user {user.employee_id} using {model_name} (Attempt {attempt}/5)...")
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=model_name,
                temperature=0.3,
                max_tokens=1000
            )
            answer = response.choices[0].message.content.strip()
            logger.info(f"LLM generation successful ({len(answer)} chars).")
            return answer
        except Exception as e:
            err_str = str(e).lower()
            is_rate_limit = any(sig in err_str for sig in ["rate limit", "429", "quota", "tokens per"])
            logger.warning(f"Groq generation attempt {attempt} ({model_name}) failed for '{query[:30]}': {e}")
            
            if is_rate_limit:
                wait_time = 5 * (2 ** (attempt - 1))  # 5s, 10s, 20s, 40s...
                logger.info(f"Rate limit hit. Pausing for {wait_time}s before retrying to avoid contaminating evaluation...")
                time.sleep(wait_time)
                continue
            
            if attempt == 5 or not is_rate_limit:
                logger.info(f"Groq failed persistently. Falling back to local Ollama ({settings.OLLAMA_MODEL})...")
                try:
                    from ollama import Client
                    ollama_client = Client(host=settings.OLLAMA_BASE_URL, timeout=60)
                    response = ollama_client.chat(
                        model=settings.OLLAMA_MODEL,
                        messages=[{"role": "user", "content": prompt}],
                        options={"temperature": 0.3, "num_predict": 1000}
                    )
                    answer = response["message"]["content"].strip()
                    logger.info(f"Ollama generation fallback successful ({len(answer)} chars).")
                    return answer
                except Exception as ollama_err:
                    logger.error(f"Ollama generation fallback failed: {ollama_err}")
            
            time.sleep(2)

    return "I apologize, but I encountered a service error while generating the response. Please try again."
