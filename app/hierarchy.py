

from collections import defaultdict
from typing import Dict, List

from .models import Employee


def resolve_managers(employees: List[Employee]) -> None:
    """
    Mutates each Employee in place, setting resolved_manager_id / manager_error
    / is_root according to the manager rules in the spec.

    Manager rows may appear before or after their reports, so we build lookup
    tables first instead of resolving in a single left-to-right pass.
    """
    by_id: Dict[str, Employee] = {e.employee_id: e for e in employees}
    by_email: Dict[str, Employee] = {e.email: e for e in employees}

    for emp in employees:
        has_id = bool(emp.manager_id)
        has_email = bool(emp.manager_email)

        if not has_id and not has_email:
            emp.is_root = True
            continue

        manager_by_id = by_id.get(emp.manager_id) if has_id else None
        manager_by_email = by_email.get(emp.manager_email) if has_email else None

        if has_id and not manager_by_id:
            emp.manager_error = f"manager_id '{emp.manager_id}' not found"
            continue
        if has_email and not manager_by_email:
            emp.manager_error = f"manager_email '{emp.manager_email}' not found"
            continue

        if has_id and has_email and manager_by_id is not manager_by_email:
            emp.manager_error = (
                f"manager_id '{emp.manager_id}' and manager_email "
                f"'{emp.manager_email}' refer to different employees"
            )
            continue

        resolved = manager_by_id if manager_by_id is not None else manager_by_email

        if resolved.employee_id == emp.employee_id:
            emp.manager_error = "employee cannot be their own manager"
            continue

        emp.resolved_manager_id = resolved.employee_id


def compute_roots(employees: List[Employee]) -> List[Employee]:
    return [e for e in employees if e.is_root]


def compute_manager_report_counts(employees: List[Employee]) -> Dict[str, int]:
    """employee_id -> number of direct reports. Only counts clean relationships
    (an employee with a manager_error contributes no relationship at all)."""
    counts: Dict[str, int] = defaultdict(int)
    for emp in employees:
        if emp.resolved_manager_id:
            counts[emp.resolved_manager_id] += 1
    return dict(counts)


def detect_cycles(employees: List[Employee]) -> set:
    
   
    by_id = {e.employee_id: e for e in employees}
    color: Dict[str, str] = {e.employee_id: "WHITE" for e in employees}
    cyclic_ids: set = set()

    def walk(start_id: str) -> None:
        path: List[str] = []  # current DFS stack, in order
        node_id = start_id

        while node_id is not None and color.get(node_id) == "WHITE":
            color[node_id] = "GRAY"
            path.append(node_id)
            node_id = by_id[node_id].resolved_manager_id

        if node_id is not None and color.get(node_id) == "GRAY":
            # Found a back-edge into the current path: everything from
            # node_id to the end of path is a cycle.
            cycle_start_index = path.index(node_id)
            for cid in path[cycle_start_index:]:
                cyclic_ids.add(cid)

        # Whole path is now fully explored; mark it BLACK so we never
        # revisit it, and so upstream callers know not to re-walk it.
        for pid in path:
            color[pid] = "BLACK"

    for emp in employees:
        if color[emp.employee_id] == "WHITE":
            walk(emp.employee_id)

    return cyclic_ids
