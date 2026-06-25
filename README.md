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
- `POST /triage/llm` accepts a ticket and returns an OpenAI structured-output triage result. It requires `OPENAI_API_KEY`; `OPENAI_MODEL` can override the default model.
- `POST /triage/hybrid` runs rules first and may call the LLM for uncertain or sensitive cases. It requires `OPENAI_API_KEY` only when LLM review is needed.

## Data

- `data/eval/triage_cases.json` contains synthetic labeled tickets for future evaluation work.

## Evaluation

```powershell
py scripts/run_triage_eval.py --mode rules
py scripts/run_triage_eval.py --mode rules --limit 5
py scripts/run_triage_eval.py --mode rules --dataset data/eval/triage_holdout_cases.json
py scripts/run_triage_eval.py --mode llm --limit 5
py scripts/run_triage_eval.py --mode llm --dataset data/eval/triage_holdout_cases.json
py scripts/run_triage_eval.py --mode hybrid --limit 5
```

Evaluation supports `rules`, `llm`, and `hybrid` modes. LLM mode requires `OPENAI_API_KEY`; hybrid mode requires it only when the hybrid path calls LLM review.

See `reports/rules_baseline_eval.md` for the first rules baseline report and failure analysis.

See `reports/rules_baseline_eval_after_tuning.md` for the tuned rules baseline report.

See `reports/rules_holdout_eval.md` for the holdout rules evaluation report.

See `reports/llm_smoke_eval.md` for the first live LLM smoke evaluation notes.

See `reports/rules_vs_llm_eval.md` for the Rules vs LLM evaluation comparison.

See `reports/rules_llm_hybrid_eval.md` for the Rules vs LLM vs Hybrid comparison.

See `docs/hybrid-triage-design.md` for the proposed hybrid triage design.
