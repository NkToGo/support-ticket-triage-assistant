# AI Support Ticket Triage Assistant

Backend foundation for experimenting with structured support ticket triage.

## Local Setup

```powershell
py -m pip install -e ".[dev]"
py -m pytest
```

ASGI app import path:

```text
support_triage.main:app
```

## API

- `GET /health` returns `{"status": "ok"}`.
- `POST /triage/rules` accepts a ticket and returns a deterministic rule-based triage result.

## Data

- `data/eval/triage_cases.json` contains synthetic labeled tickets for future evaluation work.

## Evaluation

```powershell
py scripts/run_triage_eval.py --mode rules
```

See `reports/rules_baseline_eval.md` for the first rules baseline report and failure analysis.

See `reports/rules_baseline_eval_after_tuning.md` for the tuned rules baseline report.
