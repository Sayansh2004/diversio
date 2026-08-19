# HRIS Import Preview

A small FastAPI app that lets a user upload an HRIS CSV and previews:
total source rows, accepted employees, row-level validation errors,
root employees, manager → direct-report counts, and employees that
participate in a reporting cycle.

## Why FastAPI instead of Django

The task states Django is preferred to match the team's stack, but allows
another framework if explained. I chose FastAPI because it's the framework
I have the most hands-on experience with, and this task doesn't need
Django's ORM, admin, or auth — persistence is explicitly not required and
there's no user model. The core logic (`parsing.py`, `validation.py`,
`hierarchy.py`) has zero framework imports, so porting the web layer to
Django later would be a small, contained change.

## Project layout

```
app/
  models.py       # plain dataclasses shared across modules
  parsing.py       # CSV bytes -> normalized rows (no framework code)
  validation.py    # identity rules: required fields, uniqueness
  hierarchy.py      # manager resolution, roots, report counts, cycle detection
  main.py          # FastAPI routes; thin glue over the above
  templates/       # server-rendered HTML (Jinja2), no JS framework
tests/
  test_parsing.py
  test_validation.py
  test_hierarchy.py
sample_data/
  sample.csv       # exercises every rule: duplicates, missing manager,
                    # conflicting refs, self-management, a 2-node cycle,
                    # and an employee reporting into that cycle
```

## Setup & run

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000, upload `sample_data/sample.csv` (or your own),
and view the result page.

## Running tests

```bash
pytest tests/ -v
```

24 tests covering: CSV normalization/quoting/BOM handling, malformed-file
errors, identity uniqueness rules, manager resolution (id-only,
email-only, both, conflicting, not-found, self-management), root/report-count
computation, and cycle detection (including the "reports into a cycle
without being cyclic" case).

## Approach: complexity

Let n = number of rows.

- **Parsing**: O(n) time, O(n) space — single pass over the CSV with
  Python's `csv` module.
- **Identity validation**: O(n) time/space — two dict passes to find
  duplicate ids/emails, then one pass to build accepted/rejected lists.
- **Manager resolution**: O(n) time/space — build `id -> employee` and
  `email -> employee` lookup dicts once (O(n)), then O(1) lookups per
  employee. This is why manager rows can appear before or after their
  reports.
- **Cycle detection**: O(n) time, O(n) space. Each employee has at most
  one outgoing edge (to their resolved manager), so the "reports to"
  graph has at most n edges. A standard three-color DFS (white/gray/black)
  visits each node and edge once; a back-edge onto a still-gray node marks
  exactly that node's segment of the walk as cyclic, which is what keeps
  employees who merely report into a cycle from being misclassified.

Overall the pipeline is linear, so it should scale to ~100k employees
without algorithmic changes — the practical bottleneck at that size would
be memory (holding all employees as Python objects) and Jinja2 rendering
a very large HTML table, not the analysis itself. For much larger files
I'd stream/paginate the result table rather than change the algorithms.

## Assumptions & known limitations

- If both `manager_id` and `manager_email` are given but only one matches
  an employee (the other blank or wrong), I treat that as "manager not
  found" rather than falling back to the one that matched — the spec says
  both must identify the same employee, and I read a partial match as an
  inconsistency worth surfacing rather than silently resolving.
- An employee row with a manager error still counts toward "accepted
  employees" and appears in the full employee table, but contributes to
  neither a manager's report count nor the roots list, per spec.
- Cycle detection only considers `resolved_manager_id` edges — employees
  whose manager reference itself has an error are treated as having no
  outgoing edge for cycle-detection purposes (they can't be mid-cycle
  since their manager relationship never resolved).
- No persistence: each upload is analyzed in memory and discarded;
  nothing is written to disk or a database.
- No pagination on the result table — with very large files the HTML
  response would get large. Flagged above as the main place I'd improve
  this with more time.

## Time spent

Approximately 1.5 hours.

## AI tools used

I used Claude to help scaffold the project structure and discuss
approach/trade-offs (e.g., three-color DFS vs. repeated path-walking for
cycle detection, and how to structure lookups so manager rows can appear
in any order). 
