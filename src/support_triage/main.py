from fastapi import FastAPI

from support_triage.models import TicketInput, TriageResult
from support_triage.rules import triage_with_rules

app = FastAPI(title="AI Support Ticket Triage Assistant")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/triage/rules", response_model=TriageResult)
def triage_rules(ticket: TicketInput) -> TriageResult:
    return triage_with_rules(ticket)
