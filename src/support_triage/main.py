from fastapi import FastAPI, HTTPException

from support_triage.hybrid import triage_with_hybrid
from support_triage.llm import LLMTriageConfigurationError, triage_with_llm
from support_triage.models import HybridTriageResult, TicketInput, TriageResult
from support_triage.rules import triage_with_rules

app = FastAPI(title="AI Support Ticket Triage Assistant")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/triage/rules", response_model=TriageResult)
def triage_rules(ticket: TicketInput) -> TriageResult:
    return triage_with_rules(ticket)


@app.post("/triage/llm", response_model=TriageResult)
def triage_llm(ticket: TicketInput) -> TriageResult:
    try:
        return triage_with_llm(ticket)
    except LLMTriageConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/triage/hybrid", response_model=HybridTriageResult)
def triage_hybrid(ticket: TicketInput) -> HybridTriageResult:
    try:
        return triage_with_hybrid(ticket)
    except LLMTriageConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
