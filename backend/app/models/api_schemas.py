from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

# --- Authentication Schemas ---

class LoginRequest(BaseModel):
    employee_id: str = Field(..., example="STX-E-010", description="Employee ID from the enterprise roster")

class UserProfile(BaseModel):
    employee_id: str = Field(..., example="STX-E-010")
    full_name: str = Field(..., example="Meera Nair")
    department: str = Field(..., example="Engineering")
    role_level: str = Field(..., example="Employee")
    clearance_level: int = Field(..., example=1)
    manager_id: Optional[str] = Field(None, example="STX-E-001")

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile

# --- Chat Pipeline Schemas ---

class ChatRequest(BaseModel):
    query: str = Field(..., example="What is my salary breakdown?")
    verbose: Optional[bool] = Field(False, description="If true, includes full document content in sources")

class SourceInfo(BaseModel):
    chunk_id: Optional[str] = Field(None, example="CHK-EMP-010-SAL-01")
    document_type: Optional[str] = Field(None, example="Salary Slip")
    department: Optional[str] = Field(None, example="Engineering")
    owner_name: Optional[str] = Field(None, example="Meera Nair")
    final_score: Optional[float] = Field(None, example=0.92)
    content: Optional[str] = Field(None, description="Included only if verbose=True")

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceInfo]
    intent: str
    guardrail_flags: List[str]
    response_time_ms: float

# --- User & Admin Schemas ---

class LeaveRequestItem(BaseModel):
    leave_id: Optional[str] = None
    leave_type: str
    from_date: str
    to_date: str
    duration_days: float
    reason: str
    status: str
    applied_on: str
    approved_by: Optional[str] = None

class AuditLogItem(BaseModel):
    log_id: str
    timestamp: str
    user_id: str
    tool_name: str
    arguments: Dict[str, Any]
    status: str

# --- Standard Error Schema ---

class ErrorResponse(BaseModel):
    error: str = Field(..., example="Unauthorized")
    detail: str = Field(..., example="Invalid or expired authentication token.")
    status_code: int = Field(..., example=401)
