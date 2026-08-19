"""
Identity-level validation: required fields and uniqueness of employee_id/email.

Runs before any manager/hierarchy analysis. Any row that fails here is
excluded from manager lookup entirely, per spec.
"""
from collections import defaultdict
from typing import List, Tuple

from .models import RawRow, Employee, RowError


def validate_identities(rows: List[RawRow]) -> Tuple[List[Employee], List[RowError]]:
    """
    Returns (accepted_employees, row_errors).

    A row is rejected if:
      - employee_id or email is missing, OR
      - employee_id is duplicated across rows (all such rows are invalid), OR
      - email is duplicated across rows (all such rows are invalid).
    """
    errors: List[RowError] = []

    # First pass: find which employee_ids / emails are duplicated.
    id_counts = defaultdict(list)
    email_counts = defaultdict(list)
    for row in rows:
        if row.employee_id:
            id_counts[row.employee_id].append(row)
        if row.email:
            email_counts[row.email].append(row)

    duplicate_ids = {eid for eid, occurrences in id_counts.items() if len(occurrences) > 1}
    duplicate_emails = {email for email, occurrences in email_counts.items() if len(occurrences) > 1}

    accepted: List[Employee] = []

    for row in rows:
        row_errors_for_this_row = []

        if not row.employee_id:
            row_errors_for_this_row.append("employee_id is required")
        if not row.email:
            row_errors_for_this_row.append("email is required")

        if row.employee_id and row.employee_id in duplicate_ids:
            row_errors_for_this_row.append(
                f"duplicate employee_id '{row.employee_id}'"
            )
        if row.email and row.email in duplicate_emails:
            row_errors_for_this_row.append(f"duplicate email '{row.email}'")

        if row_errors_for_this_row:
            errors.append(
                RowError(
                    source_row_number=row.source_row_number,
                    employee_id=row.employee_id,
                    message="; ".join(row_errors_for_this_row),
                )
            )
            continue

        accepted.append(
            Employee(
                source_row_number=row.source_row_number,
                employee_id=row.employee_id,
                employee_name=row.employee_name,
                email=row.email,
                manager_id=row.manager_id,
                manager_email=row.manager_email,
                department=row.department,
            )
        )

    return accepted, errors
