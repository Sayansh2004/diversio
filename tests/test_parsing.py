import pytest
from app.parsing import parse_csv_text, parse_csv_bytes, MalformedCSVError


def test_trims_whitespace_and_normalizes_case():
    text = (
        "employee_id,employee_name,email,manager_id,manager_email,department\n"
        "  E1  , Alice ,  ALICE@Example.com , , ,  Eng \n"
    )
    rows = parse_csv_text(text)
    assert len(rows) == 1
    row = rows[0]
    assert row.employee_id == "E1"          # trimmed, case preserved
    assert row.employee_name == "Alice"
    assert row.email == "alice@example.com"  # trimmed AND lowercased
    assert row.department == "Eng"


def test_quoted_commas_in_names_are_parsed_correctly():
    text = (
        "employee_id,employee_name,email,manager_id,manager_email,department\n"
        'E1,"Smith, Alice",alice@example.com,,,Eng\n'
    )
    rows = parse_csv_text(text)
    assert rows[0].employee_name == "Smith, Alice"


def test_handles_utf8_bom():
    text_with_bom = (
        "\ufeffemployee_id,employee_name,email,manager_id,manager_email,department\n"
        "E1,Alice,alice@example.com,,,Eng\n"
    )
    raw_bytes = text_with_bom.encode("utf-8")
    rows = parse_csv_bytes(raw_bytes)
    assert len(rows) == 1
    assert rows[0].employee_id == "E1"


def test_source_row_numbers_are_1_indexed_and_track_data_rows():
    text = (
        "employee_id,employee_name,email,manager_id,manager_email,department\n"
        "E1,Alice,alice@example.com,,,Eng\n"
        "E2,Bob,bob@example.com,,,Eng\n"
    )
    rows = parse_csv_text(text)
    assert [r.source_row_number for r in rows] == [1, 2]


def test_missing_required_header_raises_malformed_csv_error():
    text = "employee_id,employee_name,email,department\nE1,Alice,alice@example.com,Eng\n"
    with pytest.raises(MalformedCSVError):
        parse_csv_text(text)


def test_empty_file_raises_malformed_csv_error():
    with pytest.raises(MalformedCSVError):
        parse_csv_text("")
