"""
Turns raw CSV bytes into a list of normalized RawRow objects.

No FastAPI/Django imports here on purpose: this module should be testable
by just calling parse_csv(text) with a string.
"""
import csv
import io
from typing import List

from .models import RawRow

REQUIRED_HEADERS = {
    "employee_id",
    "employee_name",
    "email",
    "manager_id",
    "manager_email",
    "department",
}


class MalformedCSVError(Exception):
    """Raised when the upload isn't usable CSV at all (bad headers, unreadable, etc)."""
    pass


def _decode(raw_bytes: bytes) -> str:
    """Decode bytes to text, tolerating a UTF-8 BOM if present."""
    try:
        return raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise MalformedCSVError(f"File is not valid UTF-8 text: {exc}") from exc


def parse_csv_bytes(raw_bytes: bytes) -> List[RawRow]:
    """Entry point used by the web layer: bytes in, normalized rows out."""
    text = _decode(raw_bytes)
    return parse_csv_text(text)


def parse_csv_text(text: str) -> List[RawRow]:
    reader = csv.DictReader(io.StringIO(text))

    if reader.fieldnames is None:
        raise MalformedCSVError("File appears to be empty.")

    headers = {h.strip() for h in reader.fieldnames if h is not None}
    missing = REQUIRED_HEADERS - headers
    if missing:
        raise MalformedCSVError(
            f"Missing required column(s): {', '.join(sorted(missing))}"
        )

    rows: List[RawRow] = []
    # source_row_number counts data rows starting at 1 (row 1 = first data row,
    # matching what a user would call "row 1" after the header in a spreadsheet).
    for i, raw in enumerate(reader, start=1):
        try:
            rows.append(
                RawRow(
                    source_row_number=i,
                    employee_id=(raw.get("employee_id") or "").strip(),
                    employee_name=(raw.get("employee_name") or "").strip(),
                    email=(raw.get("email") or "").strip().lower(),
                    manager_id=(raw.get("manager_id") or "").strip(),
                    manager_email=(raw.get("manager_email") or "").strip().lower(),
                    department=(raw.get("department") or "").strip(),
                )
            )
        except AttributeError as exc:
            # Defensive: a malformed row (e.g. extra/missing columns) can make
            # DictReader hand back None or a list instead of a plain string.
            raise MalformedCSVError(f"Row {i} is malformed: {exc}") from exc

    return rows
