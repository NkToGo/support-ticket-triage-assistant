# Rules Baseline Evaluation Report

Date: 2026-06-14

Command:

```powershell
py scripts/run_triage_eval.py --mode rules
```

## Metric Summary

| Metric | Value |
| --- | ---: |
| total_cases | 40 |
| category_accuracy | 0.775 |
| priority_accuracy | 0.675 |
| priority_within_one_accuracy | 0.925 |
| routing_accuracy | 0.775 |
| human_review_precision | 0.692 |
| human_review_recall | 0.818 |
| human_review_f1 | 0.750 |
| critical_priority_recall | 1.000 |
| exact_match_accuracy | 0.525 |
| failures | 23 |

## Metric Interpretation

Category accuracy and routing accuracy are both 0.775. The rules baseline often gets the broad destination right, but this is not reliable enough for unattended routing.

Priority accuracy is weaker at 0.675. Priority within-one accuracy is much stronger at 0.925, which means many priority errors are near misses rather than extreme misses.

Human review recall is 0.818, while precision is 0.692. The baseline catches many cases that need review, but it also creates extra review load through false positive review triggers.

Critical priority recall is 1.000 for expected `P0` and `P1` cases. This matters because missing high-priority tickets is riskier than over-escalating some lower-priority tickets.

Exact match accuracy is 0.525. This is stricter than category accuracy because a case only counts as an exact match when category, priority, routing target, and the human-review decision are all correct.

## Representative Failures

### `billing_subscription_001`

Expected a duplicate annual charge refund to be `P2` with `billing_sensitive` review. The baseline predicted `P1` and added `priority_high`.

This shows priority over-escalation on a billing-sensitive request. The route was correct, but the priority and review reasons were too aggressive.

### `bug_report_004`

Expected a cosmetic button alignment issue to be `bug_report`, `P3`, and `engineering_triage` with no review. The baseline predicted `billing_subscription`, `P2`, and `billing_ops` because the word "Cancel" appeared as a button label.

This is a keyword collision. The rules do not distinguish UI text from billing cancellation intent.

### `performance_availability_004`

Expected a slightly slow admin page to be `P3`, routed to `support_tier_1`, with no review. The baseline predicted `P1`, routed to `incident_response`, and added `priority_high`.

This shows over-escalation from broad performance keywords without enough impact analysis.

### `data_security_privacy_003`

Expected a cross-customer data export issue to be `data_security_privacy`, `P0`, and `security_compliance`. The baseline predicted `bug_report`, `P1`, and `engineering_triage`.

This is a high-risk miss. The baseline detected product failure language but missed that the ticket describes possible data exposure.

### `other_unclear_004`

Expected an ambiguous ticket mentioning billing, login, and errors to remain `other_unclear` with low-confidence review. The baseline forced it into `account_access`.

This shows that ambiguous multi-intent tickets need stronger uncertainty handling.

## Failure Pattern Analysis

False positive human review triggers are common. Many failures include extra `low_confidence`, `ambiguous_category`, or `priority_high` reasons even when the expected review decision is false.

Priority over-escalation appears in billing, performance, technical support, feature request, and vague cases. Customer tier and broad blocking or performance terms can push cases to `P1` even when the ticket impact is routine or low.

There is category confusion between `bug_report`, `technical_support`, `billing_subscription`, and `performance_availability`. Simple keyword matching treats words like "Cancel", "export", "error", "configure", and "slow" as strong category signals without enough context.

Review reason mismatches are the most frequent failure type. Some cases have the correct category, priority, and route but still fail because the baseline adds or misses review reasons.

Vague tickets are inconsistently detected. Some low-detail tickets are correctly routed to `other_unclear`, while others are forced into a concrete category because one keyword appears in the text.

## What The Rules Baseline Does Well

- It provides a deterministic comparison point for later approaches.
- It catches all expected `P0` and `P1` cases as high priority in this run.
- It handles many obvious account access, billing, outage, and feature request cases.
- It exposes where keyword-only routing breaks down.

## What The Rules Baseline Does Poorly

- It overuses high-priority review when impact evidence is weak.
- It confuses literal UI wording with support intent.
- It has limited understanding of ambiguous or multi-intent tickets.
- It misses some security/privacy implications when the ticket also looks like a product bug.
- It does not consistently separate normal billing requests from billing-sensitive actions.

## Recommended Next Steps

- Improve keyword specificity and phrase boundaries.
- Separate billing-sensitive terms from ordinary billing terms.
- Tune priority rules so customer tier alone does not over-escalate.
- Add targeted rules for data exposure and privacy language.
- Keep this baseline as the comparison point before any later model-based or hybrid work.
