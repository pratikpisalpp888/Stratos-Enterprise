import jwt
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.config.settings import settings
from app.rbac.user_context import UserContext, load_user_context

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

ROLE_HIERARCHY: Dict[str, int] = {
    "Employee": 1,
    "Team Lead": 2,
    "Manager": 3,
    "Director": 4,
    "C-Level / VP": 5
}


def create_access_token(user: UserContext) -> str:
    """
    Creates an 8-hour JWT access token encoding the user's context.
    """
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    payload = {
        "sub": user.employee_id,
        "employee_id": user.employee_id,
        "full_name": user.full_name,
        "department": user.department,
        "role_level": user.role_level,
        "clearance_level": user.clearance_level,
        "exp": expire
    }
    encoded_jwt = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decodes and validates a JWT access token.
    Raises HTTPException(401) on failure or expiration.
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(token: str = Depends(oauth2_scheme)) -> UserContext:
    """
    FastAPI dependency that decodes JWT from Authorization header and returns UserContext.
    """
    payload = decode_access_token(token)
    employee_id = payload.get("employee_id") or payload.get("sub")
    if not employee_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing employee identification.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        user = load_user_context(employee_id)
        return user
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{employee_id}' encoded in token no longer exists in roster."
        )


def require_min_role(min_role: str):
    """
    FastAPI dependency factory enforcing minimum role level hierarchy.
    Example: require_min_role("Manager") permits Manager, Director, C-Level / VP.
    """
    min_level = ROLE_HIERARCHY.get(min_role, 1)

    def role_checker(current_user: UserContext = Depends(get_current_user)) -> UserContext:
        user_level = ROLE_HIERARCHY.get(current_user.role_level, 1)
        if user_level < min_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access Denied: Insufficient role level. Operation requires {min_role}+ privileges (your role: {current_user.role_level})."
            )
        return current_user

    return role_checker
