
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RawRow:
    """One row straight out of the CSV, after normalization but before validation."""
    source_row_number: int  # 1-based, matches what a user would see in a spreadsheet
    employee_id: str
    employee_name: str
    email: str
    manager_id: str
    manager_email: str
    department: str


@dataclass
class RowError:
    """A validation problem tied back to a specific source row."""
    source_row_number: int
    employee_id: str
    message: str


@dataclass
class Employee:
    """An accepted employee, enriched with hierarchy info as analysis proceeds."""
    source_row_number: int
    employee_id: str
    employee_name: str
    email: str
    manager_id: str
    manager_email: str
    department: str

    resolved_manager_id: Optional[str] = None  # set once manager lookup succeeds
    manager_error: Optional[str] = None        # set if manager reference is broken
    is_root: bool = False
    is_cyclic: bool = False


@dataclass
class AnalysisResult:
    """Everything the UI needs to render the import preview."""
    total_source_rows: int = 0
    accepted_employees: list = field(default_factory=list)      # list[Employee]
    row_errors: list = field(default_factory=list)               # list[RowError]
    roots: list = field(default_factory=list)                    # list[Employee]
    manager_report_counts: dict = field(default_factory=dict)    # employee_id -> count
    cyclic_employee_ids: set = field(default_factory=set)        # set[str]
