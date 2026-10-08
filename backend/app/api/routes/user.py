from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from app.models.api_schemas import UserProfile, ErrorResponse
from app.api.auth import get_current_user
from app.rbac.user_context import UserContext
from app.agents.mock_data_store import get_leave_requests

router = APIRouter(prefix="/api/v1/user", tags=["User"])


@router.get(
    "/me",
    response_model=UserProfile,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized / Missing or invalid JWT token"}
    },
    summary="Get Authenticated User Profile",
    description="Returns the profile and clearance context of the currently authenticated user."
)
def get_user_profile(current_user: UserContext = Depends(get_current_user)):
    return UserProfile(
        employee_id=current_user.employee_id,
        full_name=current_user.full_name,
        department=current_user.department,
        role_level=current_user.role_level,
        clearance_level=current_user.clearance_level,
        manager_id=current_user.manager_id
    )


@router.get(
    "/leave-requests",
    response_model=List[Dict[str, Any]],
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized / Missing or invalid JWT token"}
    },
    summary="Get Current User Leave Requests",
    description="Retrieves all leave requests filed by or associated with the current user."
)
def get_user_leave_requests(current_user: UserContext = Depends(get_current_user)):
    user_requests = get_leave_requests(current_user.employee_id)
    return user_requests
