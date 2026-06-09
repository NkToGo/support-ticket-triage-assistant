from fastapi import FastAPI

app = FastAPI(title="AI Support Ticket Triage Assistant")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
