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
