import json
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.api_schemas import ErrorResponse
from app.api.auth import require_min_role
from app.rbac.user_context import UserContext

router = APIRouter(tags=["Admin"])

AUDIT_FILE = Path(__file__).parent.parent.parent / "agents" / "data" / "audit_log.json"
REPORTS_DIR = Path(__file__).parent.parent.parent / "evaluation" / "reports"


@router.get(
    "/api/v1/admin/audit-logs",
    response_model=List[Dict[str, Any]],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized / Missing or invalid JWT token"},
        403: {"model": ErrorResponse, "description": "Forbidden: Requires Manager+ privileges"}
    },
    summary="Get Security Audit Logs",
    description="Retrieves the immutable audit trail of agentic tool execution attempts. Protected: Manager+ role required."
)
def get_audit_logs(current_user: UserContext = Depends(require_min_role("Manager"))):
    if not AUDIT_FILE.exists():
        return []
    try:
        with open(AUDIT_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read audit log: {str(e)}"
        )


@router.get(
    "/api/v1/evaluation/latest-report",
    response_model=Dict[str, Any],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized / Missing or invalid JWT token"},
        403: {"model": ErrorResponse, "description": "Forbidden: Requires Manager+ privileges"},
        404: {"model": ErrorResponse, "description": "No evaluation report found"}
    },
    summary="Get Latest Evaluation & Security Benchmark Report",
    description="Returns the latest timestamped evaluation report JSON containing RAG Quality, RBAC Integrity, and Red-Team results. Protected: Manager+ role required."
)
def get_latest_evaluation_report(current_user: UserContext = Depends(require_min_role("Manager"))):
    if not REPORTS_DIR.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No evaluation reports directory found."
        )

    report_files = sorted(REPORTS_DIR.glob("evaluation_report_*.json"), reverse=True)
    if not report_files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No evaluation report JSON files found."
        )

    try:
        with open(report_files[0], "r", encoding="utf-8") as f:
            data = json.load(f)
            return data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read latest evaluation report: {str(e)}"
        )
