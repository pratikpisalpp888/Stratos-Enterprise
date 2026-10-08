from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.guardrails.input_guardrails import run_input_guardrails
from app.guardrails.output_guardrails import run_output_guardrails
from app.rbac.user_context import load_user_context
from app.retrieval.hybrid_retriever import hybrid_search

router = APIRouter(prefix="/guardrails", tags=["Guardrails Layer"])

class InputGuardrailTestRequest(BaseModel):
    query: str

class OutputGuardrailTestRequest(BaseModel):
    generated_answer: str
    employee_id: str
    query: Optional[str] = "test retrieval query"

@router.post("/test-input")
def test_input_guardrail(request: InputGuardrailTestRequest):
    try:
        result = run_input_guardrails(request.query)
        return {
            "status": "success",
            "query": request.query,
            "guardrail_result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-output")
def test_output_guardrail(request: OutputGuardrailTestRequest):
    try:
        user = load_user_context(request.employee_id)
        # Perform retrieval to get legitimate context chunks for this user
        hybrid_res = hybrid_search(request.query or "test query", user, limit=5)
        retrieved_chunks = [r["payload"] for r in hybrid_res["results"]]
        
        result = run_output_guardrails(
            generated_answer=request.generated_answer,
            retrieved_chunks=retrieved_chunks,
            user=user
        )
        return {
            "status": "success",
            "user": {
                "employee_id": user.employee_id,
                "full_name": user.full_name,
                "department": user.department,
                "role_level": user.role_level
            },
            "query": request.query,
            "generated_answer": request.generated_answer,
            "retrieved_chunks_count": len(retrieved_chunks),
            "guardrail_result": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
