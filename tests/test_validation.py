from app.models import RawRow
from app.validation import validate_identities


def make_row(n, employee_id="E1", email="e1@example.com", manager_id="", manager_email="", name="Name"):
    return RawRow(
        source_row_number=n,
        employee_id=employee_id,
        employee_name=name,
        email=email,
        manager_id=manager_id,
        manager_email=manager_email,
        department="Eng",
    )


def test_row_missing_employee_id_is_rejected():
    rows = [make_row(1, employee_id="")]
    accepted, errors = validate_identities(rows)
    assert accepted == []
    assert len(errors) == 1
    assert "employee_id is required" in errors[0].message


def test_row_missing_email_is_rejected():
    rows = [make_row(1, email="")]
    accepted, errors = validate_identities(rows)
    assert accepted == []
    assert "email is required" in errors[0].message


def test_duplicate_employee_id_rejects_all_matching_rows():
    rows = [
        make_row(1, employee_id="E1", email="a@example.com"),
        make_row(2, employee_id="E1", email="b@example.com"),
    ]
    accepted, errors = validate_identities(rows)
    assert accepted == []
    assert len(errors) == 2
    assert {e.source_row_number for e in errors} == {1, 2}


def test_duplicate_email_rejects_all_matching_rows():
    rows = [
        make_row(1, employee_id="E1", email="same@example.com"),
        make_row(2, employee_id="E2", email="same@example.com"),
    ]
    accepted, errors = validate_identities(rows)
    assert accepted == []
    assert len(errors) == 2


def test_unique_valid_rows_are_accepted():
    rows = [
        make_row(1, employee_id="E1", email="e1@example.com"),
        make_row(2, employee_id="E2", email="e2@example.com"),
    ]
    accepted, errors = validate_identities(rows)
    assert len(accepted) == 2
    assert errors == []
