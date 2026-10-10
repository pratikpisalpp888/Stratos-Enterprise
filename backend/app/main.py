import warnings
import jwt
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.core.logging_config import get_logger
from app.models.api_schemas import ErrorResponse
from app.retrieval.sparse_retriever import build_bm25_index

from app.api.routes.auth import router as auth_router
from app.api.routes.chat import router as chat_router
from app.api.routes.user import router as user_router
from app.api.routes.admin import router as admin_router
from app.api.routes.debug import router as debug_router

warnings.filterwarnings("ignore", category=UserWarning)

logger = get_logger("app.main")

tags_metadata = [
    {
        "name": "Auth",
        "description": "JWT-based authentication endpoints for user login.",
    },
    {
        "name": "Chat",
        "description": "Production unified RAG and Agentic Chat pipeline endpoints.",
    },
    {
        "name": "User",
        "description": "Authenticated user profile and personal data endpoints.",
    },
    {
        "name": "Admin",
        "description": "Role-gated security audit logs and evaluation benchmarks (Manager+ required).",
    },
    {
        "name": "Debug",
        "description": "Internal testing and diagnostic endpoints (Development environment only).",
    },
]

app = FastAPI(
    title="SentinelRAG Enterprise API",
    description=(
        "Production-ready backend API for SentinelRAG enterprise chatbot system featuring "
        "RBAC security, multi-layered guardrails, hybrid retrieval, and agentic workflows."
    ),
    version="1.0.0",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration for Next.js Frontend (Localhost & Vercel deployments)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_origin_regex=r"^https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router Registrations
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(debug_router)


# --- Global Exception Handlers ---

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Formats all HTTPExceptions into standardized ErrorResponse JSON."""
    error_title = "HTTP Error"
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        error_title = "Unauthorized"
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        error_title = "Forbidden"
    elif exc.status_code == status.HTTP_404_NOT_FOUND:
        error_title = "Not Found"
    elif exc.status_code == status.HTTP_400_BAD_REQUEST:
        error_title = "Bad Request"

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=error_title,
            detail=str(exc.detail),
            status_code=exc.status_code
        ).model_dump()
    )


@app.exception_handler(jwt.PyJWTError)
async def jwt_exception_handler(request: Request, exc: jwt.PyJWTError):
    """Formats JWT validation errors into 401 Unauthorized ErrorResponse JSON."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=ErrorResponse(
            error="Unauthorized",
            detail=f"JWT Authentication failed: {str(exc)}",
            status_code=status.HTTP_401_UNAUTHORIZED
        ).model_dump()
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Formats ValueErrors (e.g. invalid employee IDs) into 404/400 ErrorResponse JSON."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content=ErrorResponse(
            error="Resource Not Found",
            detail=str(exc),
            status_code=status.HTTP_404_NOT_FOUND
        ).model_dump()
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Safely catches unhandled server exceptions without leaking stack traces to client."""
    logger.exception(f"Unhandled internal server error on path {request.url.path}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="Internal Server Error",
            detail="An unexpected server error occurred. Please contact system administrator.",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        ).model_dump()
    )


import asyncio
import os

@app.on_event("startup")
async def startup_event():
    logger.info("SentinelRAG API server starting up...")
    # Pre-warm BM25 in background thread so Uvicorn opens the port instantly
    def _bg_prewarm():
        try:
            build_bm25_index()
            logger.info("BM25 index successfully pre-warmed in background.")
        except Exception as e:
            logger.warning(f"Background BM25 pre-warm notice: {e}")
            
    asyncio.create_task(asyncio.to_thread(_bg_prewarm))


@app.get("/", tags=["Health"])
def root_endpoint():
    return {"status": "ok", "app": "SentinelRAG Enterprise API", "version": "1.0.0"}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "app": "SentinelRAG API", "version": "1.0.0"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, log_level="info")
