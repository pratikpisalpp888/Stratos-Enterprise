from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.rbac.user_context import load_user_context
from app.retrieval.hybrid_retriever import hybrid_search

router = APIRouter(prefix="/retrieval", tags=["Hybrid Retrieval"])

class HybridQueryRequest(BaseModel):
    employee_id: str
    query: str
    limit: Optional[int] = 5

@router.post("/hybrid-query")
def hybrid_query_endpoint(request: HybridQueryRequest):
    try:
        user = load_user_context(request.employee_id)
        result = hybrid_search(
            query=request.query,
            user=user,
            limit=request.limit or 5
        )
        return {
            "status": "success",
            "user": {
                "employee_id": user.employee_id,
                "full_name": user.full_name,
                "department": user.department,
                "role_level": user.role_level,
                "clearance_level": user.clearance_level
            },
            "query": request.query,
            "intent_classification": result["intent_classification"],
            "total_candidates": result["total_candidates"],
            "results": result["results"]
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
