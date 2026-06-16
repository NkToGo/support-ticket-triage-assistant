# Rules Holdout Evaluation Report

Date: 2026-06-16

Command:

```powershell
py scripts/run_triage_eval.py --mode rules --dataset data/eval/triage_holdout_cases.json
```

Dataset: `data/eval/triage_holdout_cases.json`

Dataset size: 24 cases

This holdout dataset is separate from the tuning dataset used by earlier reports. The goal is to check whether the deterministic rules generalize to varied wording and stress cases, not to claim broad reliability.

## Metric Summary

| Metric | Value |
| --- | ---: |
| total_cases | 24 |
| category_accuracy | 0.750 |
| priority_accuracy | 0.750 |
| priority_within_one_accuracy | 0.875 |
| routing_accuracy | 0.667 |
| human_review_precision | 0.857 |
| human_review_recall | 0.545 |
| human_review_f1 | 0.667 |
| critical_priority_recall | 0.200 |
| exact_match_accuracy | 0.542 |
| failures | 11 |

## Interpretation

The tuned rules perform worse on the holdout set than on the original dataset. This is expected for a stress dataset and is useful: it shows that the perfect score on the tuning set does not imply broad coverage.

Category and priority accuracy are both 0.750, but routing accuracy drops to 0.667. Exact match accuracy is 0.542 because exact match requires category, priority, routing target, and human-review decision to all be correct.

Human review precision is 0.857, while recall is 0.545. The rules avoid many unnecessary reviews, but they miss too many cases that should require review.

Critical priority recall is 0.200. This is the most important weak point in this run because missing `P0` and `P1` cases is higher risk than over-escalating lower-priority cases.

## Representative Failures

### `account_access_holdout_001`

Expected an expired SSO certificate blocking workspace access to be `P1`, routed to `support_tier_2`, and sent to human review. The rules predicted `P2`, routed to `support_tier_1`, and did not require review.

This shows that the current access-blocking rules miss indirect wording around SSO failures.

### `billing_subscription_holdout_001`

Expected an invoice PDF request to be a routine billing case with no review. The rules added `low_confidence` and `ambiguous_category`.

This shows that UI words such as "button" can still create false ambiguity even when the user is asking for billing help.

### `bug_report_holdout_001`

Expected wrong dashboard totals with finance impact to be a high-priority bug report. The rules predicted `other_unclear`, `P3`, and `support_tier_1`.

This shows that data correctness language can be missed when it does not use the existing bug keywords.

### `bug_report_holdout_002`

Expected a mobile layout overlap to be a low-priority bug report. The rules predicted `technical_support`.

This shows remaining category confusion between UI bug language and support/setup language.

### `bug_report_holdout_003`

Expected an API `409` response for a valid payload to be a bug report routed to engineering. The rules predicted `technical_support`.

This shows that API wording can dominate even when the ticket describes broken product behavior.

## Remaining Patterns

- Indirect access-blocking language is not reliably escalated.
- Some review-required cases are missed, especially high-priority cases.
- Product correctness bugs can be missed without familiar error words.
- API and UI wording still cause category confusion.
- Some routine tickets receive review because multiple keyword groups match.

## Next Steps

- Add targeted tests for indirect access-blocking language before changing rules.
- Improve bug detection for wrong totals, inconsistent counts, and API status codes beyond `500`/`502`.
- Refine ambiguity handling so UI words do not automatically conflict with billing intent.
- Keep the holdout dataset unchanged during the next tuning pass so it remains useful for comparison.
