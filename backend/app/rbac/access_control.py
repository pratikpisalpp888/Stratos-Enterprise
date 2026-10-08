import logging
from typing import Optional
from qdrant_client.http import models as qmodels
from app.rbac.user_context import UserContext
from app.ingestion.embedder import generate_embeddings
from app.retrieval.qdrant_client import get_client

logger = logging.getLogger("app.rbac.access_control")

COLLECTION_NAME = "stratos_documents"


def build_qdrant_filter(user: UserContext) -> qmodels.Filter:
    """
    Builds a Qdrant Filter that implements the 6-condition RBAC/ABAC
    access model. A chunk is visible if ANY condition below is true (OR/should).

    Conditions:
      1. PUBLIC ACCESS          – sensitivity_level == "Public"
      2. DEPT + CLEARANCE       – own dept, clearance sufficient, not personal
      3. CROSS-DEPT HIGH CLR    – Director/C-Level (clearance >= 3) can see all
                                  company-wide Confidential/Restricted from any dept
      4. SELF-OWNERSHIP         – owner_employee_id == user.employee_id
      5. MANAGER ACCESS         – manager_id == user.employee_id (see team's docs)
      6a. HR-ADMIN              – HR Manager+ can see docs with "HR-Admin" in access_roles
      6b. FINANCE-ADMIN         – Finance Manager+ can see docs with "Finance-Admin" in access_roles
    """

    should_clauses = []

    # ------------------------------------------------------------------
    # CONDITION 1: PUBLIC ACCESS
    # Every user sees documents marked as Public sensitivity.
    # ------------------------------------------------------------------
    should_clauses.append(
        qmodels.FieldCondition(
            key="sensitivity_level",
            match=qmodels.MatchValue(value="Public")
        )
    )

    # ------------------------------------------------------------------
    # CONDITION 2: DEPARTMENT + CLEARANCE MATCH (non-personal docs)
    # User sees company-wide docs from their own department that their
    # clearance level covers.
    # ------------------------------------------------------------------
    dept_clearance_conditions = [
        qmodels.FieldCondition(
            key="department",
            match=qmodels.MatchValue(value=user.department)
        ),
        qmodels.FieldCondition(
            key="min_clearance_level",
            range=qmodels.Range(lte=user.clearance_level)
        ),
        qmodels.FieldCondition(
            key="restricted_to_owner",
            match=qmodels.MatchValue(value=False)
        ),
    ]
    should_clauses.append(
        qmodels.Filter(must=dept_clearance_conditions)
    )

    # ------------------------------------------------------------------
    # CONDITION 3: CROSS-DEPARTMENT HIGH CLEARANCE (Director / C-Level)
    # Directors and C-Level can see Confidential/Restricted company-wide
    # docs from ANY department.
    # ------------------------------------------------------------------
    if user.clearance_level >= 3:
        cross_dept_conditions = [
            qmodels.FieldCondition(
                key="min_clearance_level",
                range=qmodels.Range(lte=user.clearance_level)
            ),
            qmodels.FieldCondition(
                key="restricted_to_owner",
                match=qmodels.MatchValue(value=False)
            ),
        ]
        should_clauses.append(
            qmodels.Filter(must=cross_dept_conditions)
        )

    # ------------------------------------------------------------------
    # CONDITION 4: SELF-OWNERSHIP
    # Users can always see their own personal documents.
    # ------------------------------------------------------------------
    should_clauses.append(
        qmodels.FieldCondition(
            key="owner_employee_id",
            match=qmodels.MatchValue(value=user.employee_id)
        )
    )

    # ------------------------------------------------------------------
    # CONDITION 5: MANAGER ACCESS
    # A user can see personal documents of their direct reports
    # (chunks where manager_id == this user's employee_id).
    # ------------------------------------------------------------------
    should_clauses.append(
        qmodels.FieldCondition(
            key="manager_id",
            match=qmodels.MatchValue(value=user.employee_id)
        )
    )

    # ------------------------------------------------------------------
    # CONDITION 6a: HR-ADMIN PRIVILEGE
    # HR Managers/Directors can see all personal docs tagged "HR-Admin"
    # in access_roles (covers appraisals, leave records, salary slips).
    # ------------------------------------------------------------------
    if user.is_hr_admin:
        should_clauses.append(
            qmodels.FieldCondition(
                key="access_roles",
                match=qmodels.MatchAny(any=["HR-Admin"])
            )
        )

    # ------------------------------------------------------------------
    # CONDITION 6b: FINANCE-ADMIN PRIVILEGE
    # Finance Managers/Directors can see personal docs tagged "Finance-Admin"
    # in access_roles (specifically Salary Slips of Finance dept employees).
    # ------------------------------------------------------------------
    if user.is_finance_admin:
        should_clauses.append(
            qmodels.FieldCondition(
                key="access_roles",
                match=qmodels.MatchAny(any=["Finance-Admin"])
            )
        )

    return qmodels.Filter(should=should_clauses)


def search_with_rbac(
    query: str,
    user: UserContext,
    limit: int = 5
) -> list[dict]:
    """
    Runs a semantic search in Qdrant with RBAC-aware filtering.
    Returns a list of result dicts with score, payload, and truncated content.
    """
    # 1. Generate query embedding
    query_vector = generate_embeddings([query])[0]

    # 2. Build access filter for this user
    access_filter = build_qdrant_filter(user)

    # 3. Query Qdrant
    client = get_client()
    try:
        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=access_filter,
            limit=limit
        ).points
    except Exception as e:
        logger.error(f"Qdrant search failed for user {user.employee_id}: {e}")
        raise

    # 4. Format results
    formatted = []
    for hit in results:
        payload = hit.payload or {}
        formatted.append({
            "score": round(hit.score, 6),
            "chunk_id": payload.get("chunk_id"),
            "content": payload.get("content", ""),
            "content_preview": payload.get("content", "")[:200],
            "document_type": payload.get("document_type"),
            "department": payload.get("department"),
            "sensitivity_level": payload.get("sensitivity_level"),
            "owner_employee_id": payload.get("owner_employee_id"),
            "owner_name": payload.get("owner_name"),
            "restricted_to_owner": payload.get("restricted_to_owner"),
            "min_clearance_level": payload.get("min_clearance_level"),
            "manager_id": payload.get("manager_id"),
            "access_roles": payload.get("access_roles"),
            "source_file": payload.get("source_file", "").split("\\")[-1],
        })

    logger.info(
        f"RBAC search for {user.employee_id} ({user.role_level}/{user.department})"
        f" | query='{query[:40]}' | results={len(formatted)}"
    )
    return formatted
