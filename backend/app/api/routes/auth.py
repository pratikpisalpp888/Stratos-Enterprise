from fastapi import APIRouter, HTTPException, status
from app.models.api_schemas import LoginRequest, LoginResponse, UserProfile, ErrorResponse
from app.rbac.user_context import load_user_context
from app.api.auth import create_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@router.post(
    "/login",
    response_model=LoginResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Employee ID not found in enterprise roster"},
        400: {"model": ErrorResponse, "description": "Invalid login request"}
    },
    summary="Mock JWT Authentication Login",
    description="Validates employee_id against enterprise roster and returns a signed 8-hour JWT token."
)
def login(req: LoginRequest):
    employee_id = req.employee_id.strip()
    if not employee_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Employee ID cannot be empty."
        )

    try:
        user = load_user_context(employee_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Employee ID '{employee_id}' not found in enterprise roster."
        )

    token = create_access_token(user)
    user_profile = UserProfile(
        employee_id=user.employee_id,
        full_name=user.full_name,
        department=user.department,
        role_level=user.role_level,
        clearance_level=user.clearance_level,
        manager_id=user.manager_id
    )

    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=user_profile
    )
