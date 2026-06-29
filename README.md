# AI Support Ticket Triage Assistant

Backend-first Applied AI project for structured support ticket triage. The system accepts a support ticket and returns typed triage output: category, priority, routing target, human-review decision, review reasons, confidence, and rationale.

## Local Setup

```powershell
py -m pip install -e ".[dev]"
py -m pytest
```

ASGI app import path:

```text
support_triage.main:app
```

## Local API Demo

```powershell
py -m pip install -e ".[dev]"
py -m uvicorn support_triage.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive FastAPI API documentation.

## Triage Modes

- `rules`: deterministic keyword and priority rules for a transparent baseline.
- `llm`: OpenAI structured-output triage using the shared `TriageResult` schema.
- `hybrid`: rules-first triage that calls LLM review only for uncertain or sensitive cases.

## API

- `GET /health` returns `{"status": "ok"}`.
- `POST /triage/rules` accepts a ticket and returns a deterministic rule-based `TriageResult`.
- `POST /triage/llm` accepts a ticket and returns an OpenAI structured-output `TriageResult`.
- `POST /triage/hybrid` accepts a ticket and returns a hybrid wrapper with the final triage result, rules result, optional LLM result, and disagreement details.

LLM-backed paths use environment configuration. `POST /triage/llm` requires `OPENAI_API_KEY`; `OPENAI_MODEL` can override the default model. `POST /triage/hybrid` requires `OPENAI_API_KEY` only when LLM review is triggered.

## Data

- `data/eval/triage_cases.json` contains 40 synthetic labeled tickets used for baseline development and comparison.
- `data/eval/triage_holdout_cases.json` contains 24 synthetic labeled holdout tickets for stress and generalization checks.

## Evaluation

```powershell
py scripts/run_triage_eval.py --mode rules
py scripts/run_triage_eval.py --mode rules --dataset data/eval/triage_holdout_cases.json
py scripts/run_triage_eval.py --mode llm --limit 5
py scripts/run_triage_eval.py --mode hybrid --limit 5
```

Evaluation supports `rules`, `llm`, and `hybrid` modes. `llm` mode can call the OpenAI API. `hybrid` mode can call the OpenAI API when the hybrid decision path needs LLM review.

## Reports

- `reports/rules_baseline_eval.md`: initial rules baseline metrics and failure analysis.
- `reports/rules_baseline_eval_after_tuning.md`: targeted rules tuning results.
- `reports/rules_holdout_eval.md`: rules evaluation on the holdout dataset.
- `reports/llm_smoke_eval.md`: first live LLM smoke evaluation notes.
- `reports/rules_vs_llm_eval.md`: rules and LLM comparison.
- `reports/rules_llm_hybrid_eval.md`: rules, LLM, and hybrid comparison.
- `docs/hybrid-triage-design.md`: design notes for the conservative hybrid approach.

## CI

GitHub Actions installs the package with dev dependencies, runs `python -m pytest`, and runs a non-LLM rules evaluation smoke check:

```powershell
python scripts/run_triage_eval.py --mode rules --limit 5
```

CI does not require `OPENAI_API_KEY` and does not run live LLM or hybrid evaluation.

## Limitations

- Evaluation datasets are synthetic and intentionally small.
- The system does not autonomously resolve tickets.
- The system does not generate customer-facing replies.
- The current work does not make a production-readiness claim.
- Human review remains important for sensitive or high-risk cases.
