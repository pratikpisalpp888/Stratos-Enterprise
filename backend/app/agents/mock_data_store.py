import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any

logger = logging.getLogger("app.agents.mock_data_store")

DATA_DIR = Path(__file__).parent / "data"
LEAVE_FILE = DATA_DIR / "leave_requests.json"

def _ensure_data_file() -> List[Dict[str, Any]]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not LEAVE_FILE.exists():
        with open(LEAVE_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        return []
    try:
        with open(LEAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading {LEAVE_FILE}: {e}")
        return []

def _save_data(data: List[Dict[str, Any]]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(LEAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def create_leave_request(employee_id: str, start_date: str, end_date: str, reason: str) -> Dict[str, Any]:
    """
    Creates a new pending leave request for employee_id and persists to JSON.
    """
    requests = _ensure_data_file()
    req_num = len(requests) + 1001
    request_id = f"LR-{req_num}"
    
    new_request = {
        "request_id": request_id,
        "employee_id": employee_id,
        "start_date": start_date,
        "end_date": end_date,
        "reason": reason,
        "status": "Pending",
        "approved_by": None,
        "created_at": datetime.now().isoformat()
    }
    
    requests.append(new_request)
    _save_data(requests)
    logger.info(f"Created leave request {request_id} for employee {employee_id}")
    return new_request

def get_leave_requests(employee_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Retrieves all leave requests, optionally filtered by employee_id.
    """
    requests = _ensure_data_file()
    if employee_id:
        return [r for r in requests if r.get("employee_id") == employee_id]
    return requests

def get_leave_request_by_id(request_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a specific leave request by request_id.
    """
    requests = _ensure_data_file()
    for r in requests:
        if r.get("request_id") == request_id:
            return r
    return None

def update_leave_request_status(request_id: str, status: str, approved_by: str) -> Optional[Dict[str, Any]]:
    """
    Updates the status ('Approved' / 'Rejected') of a leave request.
    """
    requests = _ensure_data_file()
    for r in requests:
        if r.get("request_id") == request_id:
            r["status"] = status
            r["approved_by"] = approved_by
            r["updated_at"] = datetime.now().isoformat()
            _save_data(requests)
            logger.info(f"Updated leave request {request_id} status to '{status}' by {approved_by}")
            return r
    logger.warning(f"Leave request {request_id} not found for status update.")
    return None
