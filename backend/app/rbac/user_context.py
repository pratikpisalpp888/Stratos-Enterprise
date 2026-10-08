import json
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, model_validator
from app.config.settings import settings

logger = logging.getLogger("app.rbac.user_context")

# Role -> numeric clearance level (mirrors document min_clearance_level scale)
ROLE_CLEARANCE_MAP = {
    "Intern": 0,
    "Employee": 0,
    "Team Lead": 1,
    "Manager": 2,
    "Director": 3,
    "C-Level": 3,
}

import threading

# Lazy-loaded roster index: {employee_id -> employee_dict}
_roster_index: Optional[dict] = None
_roster_lock = threading.Lock()

def _get_roster() -> dict:
    global _roster_index
    with _roster_lock:
        if _roster_index is None:
            temp_roster = {}
            roster_dir: Path = settings.EMPLOYEE_ROSTER_DIR
            for f in roster_dir.glob("*.json"):
                try:
                    data = json.load(open(f, encoding="utf-8"))
                    for emp in data:
                        eid = emp.get("employee_id")
                        if eid:
                            temp_roster[eid] = emp
                except Exception as e:
                    logger.error(f"Failed to load roster file {f.name}: {e}")
            _roster_index = temp_roster
            logger.info(f"Roster index loaded with {len(_roster_index)} employees.")
    return _roster_index


class UserContext(BaseModel):
    employee_id: str
    full_name: str
    department: str
    role_level: str
    designation: str
    manager_id: Optional[str] = None
    clearance_level: int = 0  # Derived from role_level

    @model_validator(mode="after")
    def derive_clearance(self) -> "UserContext":
        self.clearance_level = ROLE_CLEARANCE_MAP.get(self.role_level, 0)
        return self

    @property
    def is_hr_admin(self) -> bool:
        """True if this user has HR-Admin privileges (HR dept, Manager+)."""
        return (
            self.department == "HR"
            and self.role_level in {"Manager", "Director", "C-Level"}
        )

    @property
    def is_finance_admin(self) -> bool:
        """True if this user has Finance-Admin privileges (Finance dept, Manager+)."""
        return (
            self.department == "Finance"
            and self.role_level in {"Manager", "Director", "C-Level"}
        )


def load_user_context(employee_id: str) -> UserContext:
    """
    Looks up an employee by ID from the merged Employee_roaster and
    returns their full UserContext (including derived clearance_level).
    Raises ValueError if the employee is not found.
    """
    roster = _get_roster()
    emp = roster.get(employee_id)
    if emp is None:
        raise ValueError(
            f"Employee '{employee_id}' not found in roster. "
            f"Available IDs: {list(roster.keys())[:5]}..."
        )
    return UserContext(
        employee_id=emp["employee_id"],
        full_name=emp["full_name"],
        department=emp["department"],
        role_level=emp["role_level"],
        designation=emp["designation"],
        manager_id=emp.get("manager_id"),
    )
