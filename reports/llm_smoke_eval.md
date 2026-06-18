# LLM Smoke Evaluation Report

Date: 2026-06-18

This report documents the first manually observed live LLM smoke evaluation runs. The purpose was to confirm that the LLM evaluation path can execute against small dataset subsets and return structured metrics.

This is not a full model-quality evaluation. Each run used only 5 cases.

Model: `gpt-4.1-mini` via `OPENAI_MODEL`

`OPENAI_API_KEY` was set locally for the manual run. The key is not stored in this repository.

## Run 1: Original Dataset Smoke Test

Command:

```powershell
py scripts/run_triage_eval.py --mode llm --limit 5
```

Dataset: `data/eval/triage_cases.json`

## Metric Summary

| Metric | Value |
| --- | ---: |
| total_cases | 5 |
| category_accuracy | 1.000 |
| priority_accuracy | 1.000 |
| priority_within_one_accuracy | 1.000 |
| routing_accuracy | 1.000 |
| human_review_precision | 1.000 |
| human_review_recall | 1.000 |
| human_review_f1 | 1.000 |
| critical_priority_recall | 1.000 |
| exact_match_accuracy | 1.000 |
| failures | 0 |

## Run 2: Holdout Dataset Smoke Test

Command:

```powershell
py scripts/run_triage_eval.py --mode llm --dataset data/eval/triage_holdout_cases.json --limit 5
```

Dataset: `data/eval/triage_holdout_cases.json`

## Metric Summary

| Metric | Value |
| --- | ---: |
| total_cases | 5 |
| category_accuracy | 0.800 |
| priority_accuracy | 0.600 |
| priority_within_one_accuracy | 1.000 |
| routing_accuracy | 0.600 |
| human_review_precision | 1.000 |
| human_review_recall | 1.000 |
| human_review_f1 | 1.000 |
| critical_priority_recall | 1.000 |
| exact_match_accuracy | 0.400 |
| failures | 3 |

## Interpretation

The first 5 cases from the original dataset were all classified, prioritized, routed, and reviewed as expected. This confirms that the live LLM path can produce valid structured outputs for a small subset.

The first 5 holdout cases exposed category, priority, and routing misses. Human-review precision, recall, and F1 were perfect in this tiny sample, but the sample is too small to infer reliable review performance.

Exact match accuracy is stricter than category accuracy because it requires category, priority, routing target, and human-review decision to all align.

## Representative Holdout Failures

### `account_access_holdout_002`

Subject: Invite link question

Expected:

- category: `account_access`
- priority: `P2`
- routing_target: `support_tier_1`

Predicted:

- category: `feature_request`
- priority: `P3`
- routing_target: `product_management`

Mismatched fields: `category`, `priority`, `routing_target`

### `account_access_holdout_003`

Subject: Manager keeps seeing MFA prompt

Expected:

- routing_target: `support_tier_1`

Predicted:

- routing_target: `support_tier_2`

Mismatched fields: `routing_target`

### `billing_subscription_holdout_001`

Subject: Invoice PDF button question

Expected:

- priority: `P2`

Predicted:

- priority: `P3`

Mismatched fields: `priority`

## Limitations

This report covers two 5-case smoke tests only. It should be used as an execution sanity check, not as evidence of broad model reliability or production readiness.

The holdout result is especially useful because it shows that even a successful structured-output run can still make meaningful triage mistakes.

## Recommended Next Step

Run a larger intentional LLM evaluation later, likely with `--limit 10` first and then the full dataset. After that run, create a comparison report that contrasts rules and LLM behavior across the same dataset.
