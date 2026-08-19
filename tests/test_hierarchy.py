from app.models import Employee
from app.hierarchy import (
    resolve_managers,
    compute_roots,
    compute_manager_report_counts,
    detect_cycles,
)


def make_emp(n, employee_id, email, manager_id="", manager_email="", name=None):
    return Employee(
        source_row_number=n,
        employee_id=employee_id,
        employee_name=name or employee_id,
        email=email,
        manager_id=manager_id,
        manager_email=manager_email,
        department="Eng",
    )


def test_employee_with_no_manager_fields_is_root():
    emp = make_emp(1, "E1", "e1@example.com")
    resolve_managers([emp])
    assert emp.is_root is True
    assert emp.manager_error is None


def test_manager_resolved_by_id_only():
    boss = make_emp(1, "M1", "m1@example.com")
    report = make_emp(2, "E1", "e1@example.com", manager_id="M1")
    resolve_managers([boss, report])
    assert report.resolved_manager_id == "M1"
    assert report.manager_error is None


def test_manager_resolved_by_email_only():
    boss = make_emp(1, "M1", "m1@example.com")
    report = make_emp(2, "E1", "e1@example.com", manager_email="m1@example.com")
    resolve_managers([boss, report])
    assert report.resolved_manager_id == "M1"


def test_manager_can_appear_after_report_in_file_order():
    report = make_emp(1, "E1", "e1@example.com", manager_id="M1")
    boss = make_emp(2, "M1", "m1@example.com")
    resolve_managers([report, boss])  # report listed first
    assert report.resolved_manager_id == "M1"


def test_conflicting_manager_id_and_email_is_an_error():
    boss1 = make_emp(1, "M1", "m1@example.com")
    boss2 = make_emp(2, "M2", "m2@example.com")
    report = make_emp(3, "E1", "e1@example.com", manager_id="M1", manager_email="m2@example.com")
    resolve_managers([boss1, boss2, report])
    assert report.manager_error is not None
    assert report.resolved_manager_id is None


def test_manager_not_found_is_an_error():
    report = make_emp(1, "E1", "e1@example.com", manager_id="GHOST")
    resolve_managers([report])
    assert "not found" in report.manager_error


def test_self_management_is_an_error():
    emp = make_emp(1, "E1", "e1@example.com", manager_id="E1")
    resolve_managers([emp])
    assert emp.manager_error == "employee cannot be their own manager"
    assert emp.resolved_manager_id is None


def test_employee_with_manager_error_is_not_root_and_has_no_relationship():
    emp = make_emp(1, "E1", "e1@example.com", manager_id="GHOST")
    resolve_managers([emp])
    assert emp.is_root is False
    counts = compute_manager_report_counts([emp])
    assert counts == {}


def test_manager_report_counts_are_correct():
    boss = make_emp(1, "M1", "m1@example.com")
    r1 = make_emp(2, "E1", "e1@example.com", manager_id="M1")
    r2 = make_emp(3, "E2", "e2@example.com", manager_id="M1")
    employees = [boss, r1, r2]
    resolve_managers(employees)
    counts = compute_manager_report_counts(employees)
    assert counts == {"M1": 2}


def test_roots_are_computed_correctly():
    root = make_emp(1, "E1", "e1@example.com")
    report = make_emp(2, "E2", "e2@example.com", manager_id="E1")
    employees = [root, report]
    resolve_managers(employees)
    roots = compute_roots(employees)
    assert roots == [root]


def test_simple_two_node_cycle_is_detected():
    a = make_emp(1, "A", "a@example.com", manager_id="B")
    b = make_emp(2, "B", "b@example.com", manager_id="A")
    employees = [a, b]
    resolve_managers(employees)
    cyclic = detect_cycles(employees)
    assert cyclic == {"A", "B"}


def test_employee_reporting_into_a_cycle_is_not_flagged_cyclic():
    # C -> A -> B -> A  (A and B form a cycle; C merely reports into it)
    a = make_emp(1, "A", "a@example.com", manager_id="B")
    b = make_emp(2, "B", "b@example.com", manager_id="A")
    c = make_emp(3, "C", "c@example.com", manager_id="A")
    employees = [a, b, c]
    resolve_managers(employees)
    cyclic = detect_cycles(employees)
    assert cyclic == {"A", "B"}
    assert "C" not in cyclic


def test_no_cycle_in_a_clean_tree():
    root = make_emp(1, "A", "a@example.com")
    child = make_emp(2, "B", "b@example.com", manager_id="A")
    grandchild = make_emp(3, "C", "c@example.com", manager_id="B")
    employees = [root, child, grandchild]
    resolve_managers(employees)
    assert detect_cycles(employees) == set()
