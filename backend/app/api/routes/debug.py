from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Optional
from app.config.settings import settings
from app.rbac.user_context import load_user_context, UserContext
from app.rbac.access_control import search_with_rbac
from app.retrieval.hybrid_retriever import hybrid_search
from app.guardrails.input_guardrails import run_input_guardrails
from app.guardrails.output_guardrails import run_output_guardrails

def verify_dev_env():
    if settings.APP_ENV.lower() not in ["development", "dev", "local"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Debug endpoints are disabled in non-development environments."
        )

router = APIRouter(
    prefix="/api/v1/debug",
    tags=["Debug"],
    dependencies=[Depends(verify_dev_env)]
)


class RBACQueryRequest(BaseModel):
    employee_id: str
    query: str
    limit: Optional[int] = 5


class HybridQueryRequest(BaseModel):
    employee_id: str
    query: str
    limit: Optional[int] = 5


class InputGuardrailTestRequest(BaseModel):
    query: str


class OutputGuardrailTestRequest(BaseModel):
    generated_answer: str
    employee_id: str
    query: Optional[str] = "test retrieval query"


@router.get("/user-context/{employee_id}", summary="[DEBUG] Inspect UserContext")
def get_user_context_debug(employee_id: str):
    try:
        return load_user_context(employee_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/rbac/query", summary="[DEBUG] Raw RBAC Query")
def rbac_query_debug(request: RBACQueryRequest):
    try:
        user = load_user_context(request.employee_id)
        results = search_with_rbac(query=request.query, user=user, limit=request.limit or 5)
        return {
            "status": "success",
            "user": {
                "employee_id": user.employee_id,
                "full_name": user.full_name,
                "department": user.department,
                "role_level": user.role_level
            },
            "query": request.query,
            "result_count": len(results),
            "results": results
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/retrieval/hybrid-query", summary="[DEBUG] Raw Hybrid Search")
def hybrid_query_debug(request: HybridQueryRequest):
    try:
        user = load_user_context(request.employee_id)
        result = hybrid_search(query=request.query, user=user, limit=request.limit or 5)
        return {
            "status": "success",
            "user": {
                "employee_id": user.employee_id,
                "full_name": user.full_name,
                "department": user.department
            },
            "query": request.query,
            "intent_classification": result["intent_classification"],
            "total_candidates": result["total_candidates"],
            "results": result["results"]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/guardrails/test-input", summary="[DEBUG] Test Input Guardrails")
def test_input_guardrail_debug(request: InputGuardrailTestRequest):
    result = run_input_guardrails(request.query)
    return {"status": "success", "query": request.query, "guardrail_result": result}


@router.post("/guardrails/test-output", summary="[DEBUG] Test Output Guardrails")
def test_output_guardrail_debug(request: OutputGuardrailTestRequest):
    try:
        user = load_user_context(request.employee_id)
        hybrid_res = hybrid_search(request.query or "test query", user, limit=5)
        retrieved_chunks = [r["payload"] for r in hybrid_res["results"]]
        result = run_output_guardrails(
            generated_answer=request.generated_answer,
            retrieved_chunks=retrieved_chunks,
            user=user
        )
        return {"status": "success", "user": user.employee_id, "guardrail_result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
