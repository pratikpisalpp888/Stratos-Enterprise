import re
import json
import logging
from pathlib import Path
from app.config.settings import settings

logger = logging.getLogger("app.ingestion.payload_builder")

# Lazy-loaded Employee Roster index
_employee_roster = None

def _get_employee_roster() -> dict:
    global _employee_roster
    if _employee_roster is None:
        _employee_roster = {}
        roster_dir = settings.EMPLOYEE_ROSTER_DIR
        if roster_dir.exists():
            for f in roster_dir.glob("*.json"):
                try:
                    with open(f, "r", encoding="utf-8") as file:
                        data = json.load(file)
                        for emp in data:
                            emp_id = emp.get("employee_id")
                            if emp_id:
                                _employee_roster[emp_id] = emp
                except Exception as e:
                    logger.error(f"Failed to read roster file {f}: {e}")
        roster_size = len(_employee_roster)
        logger.info(f"Loaded {roster_size} employees into payload_builder index.")
    return _employee_roster

def build_payload(chunk: dict) -> dict:
    metadata = chunk.get("metadata", {})
    chunk_id = chunk.get("chunk_id", "")
    
    # Parse chunk_index from chunk_id (e.g. filename.txt_chunk_3)
    chunk_index = 0
    match = re.search(r"_chunk_(\d+)$", chunk_id)
    if match:
        chunk_index = int(match.group(1))
        
    owner_employee_id = metadata.get("Owner_Employee_ID") or metadata.get("Owner_Employee_ID_") or None
    owner_name = metadata.get("Owner_Name") or None
    
    is_personal = owner_employee_id is not None
    manager_id = None
    
    if is_personal:
        # Resolve department and manager_id from roster
        roster = _get_employee_roster()
        emp_info = roster.get(owner_employee_id)
        if emp_info:
            department = emp_info.get("department")
            manager_id = emp_info.get("manager_id") or None
        else:
            # Fallback to metadata if employee not found in roster
            department = metadata.get("Department") or None
    else:
        department = metadata.get("Department") or None
        
    sensitivity_level = metadata.get("Sensitivity_Level") or "Internal"
    
    # Calculate derived fields
    min_clearance_level = settings.CLEARANCE_LEVELS.get(sensitivity_level, 1) # Default Internal (1)
    restricted_to_owner = is_personal
    
    # access_roles: ensure it is a list and defaults for personal docs
    access_roles = metadata.get("Access_Roles")
    if not access_roles:
        access_roles = []
    elif isinstance(access_roles, str):
        access_roles = [r.strip() for r in access_roles.replace("[", "").replace("]", "").split(",") if r.strip() and r.strip() != "None"]
    elif isinstance(access_roles, list):
        access_roles = [r for r in access_roles if r != "None"]
        
    if is_personal:
        doc_type_val = metadata.get("Document_Type") or ""
        if doc_type_val in ["Salary Slip", "Expense Record", "Financial Record"]:
            if "Finance-Admin" not in access_roles:
                access_roles.append("Finance-Admin")
            if "HR-Admin" not in access_roles:
                access_roles.append("HR-Admin")
        else:
            # Appraisals, Leave Records, HR docs
            if "HR-Admin" not in access_roles:
                access_roles.append("HR-Admin")
        
    payload = {
        "chunk_id": chunk_id,
        "content": chunk.get("content", ""),
        "source_file": chunk.get("source_file", ""),
        "document_type": metadata.get("Document_Type") or None,
        "department": department,
        "sensitivity_level": sensitivity_level,
        "owner_employee_id": owner_employee_id,
        "owner_name": owner_name,
        "access_roles": access_roles,
        "manager_id": manager_id,
        "author": metadata.get("Author") or None,
        "created_date": metadata.get("Created_Date") or None,
        "chunk_index": chunk_index,
        "min_clearance_level": min_clearance_level,
        "restricted_to_owner": restricted_to_owner
    }
    
    return payload
