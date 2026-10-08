from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from app.rbac.user_context import load_user_context, UserContext
from app.rbac.access_control import search_with_rbac

router = APIRouter(prefix="/rbac", tags=["RBAC"])

class RBACQueryRequest(BaseModel):
    employee_id: str
    query: str
    limit: Optional[int] = 5

@router.get("/user-context/{employee_id}", response_model=UserContext)
def get_user_context(employee_id: str):
    try:
        context = load_user_context(employee_id)
        return context
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query")
def rbac_query(request: RBACQueryRequest):
    try:
        user = load_user_context(request.employee_id)
        results = search_with_rbac(
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
            "result_count": len(results),
            "results": results
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
