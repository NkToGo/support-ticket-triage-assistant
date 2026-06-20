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

## Data

- `data/eval/triage_cases.json` contains synthetic labeled tickets for future evaluation work.

## Evaluation

```powershell
py scripts/run_triage_eval.py --mode rules
py scripts/run_triage_eval.py --mode rules --limit 5
py scripts/run_triage_eval.py --mode rules --dataset data/eval/triage_holdout_cases.json
py scripts/run_triage_eval.py --mode llm --limit 5
py scripts/run_triage_eval.py --mode llm --dataset data/eval/triage_holdout_cases.json
```

LLM evaluation requires `OPENAI_API_KEY` and may call the OpenAI API.

See `reports/rules_baseline_eval.md` for the first rules baseline report and failure analysis.

See `reports/rules_baseline_eval_after_tuning.md` for the tuned rules baseline report.

See `reports/rules_holdout_eval.md` for the holdout rules evaluation report.

See `reports/llm_smoke_eval.md` for the first live LLM smoke evaluation notes.

See `reports/rules_vs_llm_eval.md` for the Rules vs LLM evaluation comparison.
