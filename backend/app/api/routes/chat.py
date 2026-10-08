from fastapi import APIRouter, Depends, HTTPException, status
from app.models.api_schemas import ChatRequest, ChatResponse, SourceInfo, ErrorResponse
from app.api.auth import get_current_user
from app.rbac.user_context import UserContext
from app.agents.agent_orchestrator import run_agent_pipeline

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


@router.post(
    "/query",
    response_model=ChatResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized / Missing or invalid JWT token"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    },
    summary="Execute Unified RAG & Agentic Chat Pipeline",
    description="Processes user query through intent routing, RBAC retrieval, agent tool execution, and guardrails. Uses authenticated JWT token."
)
def chat_query_endpoint(
    request: ChatRequest,
    current_user: UserContext = Depends(get_current_user)
):
    try:
        pipeline_result = run_agent_pipeline(
            query=request.query,
            employee_id=current_user.employee_id
        )

        raw_sources = pipeline_result.get("sources", [])
        formatted_sources = []

        for s in raw_sources:
            formatted_sources.append(
                SourceInfo(
                    chunk_id=s.get("chunk_id"),
                    document_type=s.get("document_type"),
                    department=s.get("department"),
                    owner_name=s.get("owner_name"),
                    final_score=s.get("final_score"),
                    content=s.get("content") if request.verbose else None
                )
            )

        intent_str = "general_query"
        intent_info = pipeline_result.get("intent_classification")
        if isinstance(intent_info, dict):
            intent_str = intent_info.get("intent", "general_query")

        return ChatResponse(
            answer=pipeline_result.get("answer", ""),
            sources=formatted_sources,
            intent=intent_str,
            guardrail_flags=pipeline_result.get("guardrail_flags", []),
            response_time_ms=float(pipeline_result.get("response_time_ms", 0.0))
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat pipeline processing error: {str(e)}"
        )
