"""
FastAPI web layer. Deliberately thin: it only reads the upload, calls into
parsing/validation/hierarchy, and renders the result. No business logic here.
"""
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .parsing import parse_csv_bytes, MalformedCSVError
from .validation import validate_identities
from .hierarchy import (
    resolve_managers,
    compute_roots,
    compute_manager_report_counts,
    detect_cycles,
)
from .models import AnalysisResult

app = FastAPI(title="HRIS Import Preview")
templates = Jinja2Templates(directory="app/templates")


def run_analysis(raw_bytes: bytes) -> AnalysisResult:
    """Pure orchestration: bytes in, AnalysisResult out. Easy to unit test."""
    rows = parse_csv_bytes(raw_bytes)  # may raise MalformedCSVError

    accepted, row_errors = validate_identities(rows)
    resolve_managers(accepted)

    roots = compute_roots(accepted)
    report_counts = compute_manager_report_counts(accepted)
    cyclic_ids = detect_cycles(accepted)
    for emp in accepted:
        emp.is_cyclic = emp.employee_id in cyclic_ids

    return AnalysisResult(
        total_source_rows=len(rows),
        accepted_employees=accepted,
        row_errors=row_errors,
        roots=roots,
        manager_report_counts=report_counts,
        cyclic_employee_ids=cyclic_ids,
    )


@app.get("/", response_class=HTMLResponse)
async def upload_form(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/upload", response_class=HTMLResponse)
async def upload_csv(request: Request, file: UploadFile = File(...)):
    raw_bytes = await file.read()

    try:
        result = run_analysis(raw_bytes)
    except MalformedCSVError as exc:
        return templates.TemplateResponse(
            "index.html",
            {"request": request, "error": str(exc)},
        )

    return templates.TemplateResponse(
        "result.html",
        {
            "request": request,
            "filename": file.filename,
            "result": result,
        },
    )
