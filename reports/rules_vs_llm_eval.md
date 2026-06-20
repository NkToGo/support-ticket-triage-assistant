# Rules vs LLM Evaluation Comparison

Date: 2026-06-18

This report compares the deterministic rules baseline with the structured-output LLM triage path on the original and holdout evaluation datasets. The LLM runs were performed manually with local OpenAI credentials. No API key is stored in this repository.

The results use synthetic labeled datasets. They are useful for comparing behavior in this project, but they are not a broad production-quality claim.

LLM model: `gpt-4.1-mini` via `OPENAI_MODEL`

## Commands

Rules on original dataset:

```powershell
py scripts/run_triage_eval.py --mode rules
```

Rules on holdout dataset:

```powershell
py scripts/run_triage_eval.py --mode rules --dataset data/eval/triage_holdout_cases.json
```

LLM on original dataset:

```powershell
py scripts/run_triage_eval.py --mode llm
```

LLM on holdout dataset:

```powershell
py scripts/run_triage_eval.py --mode llm --dataset data/eval/triage_holdout_cases.json
```

## Datasets

| Dataset | File | Cases | Notes |
| --- | --- | ---: | --- |
| Original | `data/eval/triage_cases.json` | 40 | The rules were tuned against this dataset. |
| Holdout | `data/eval/triage_holdout_cases.json` | 24 | Separate stress dataset for checking generalization. |

Holdout results are more useful for judging generalization than the tuned original dataset.

## Original Dataset Comparison

| Metric | Rules | LLM |
| --- | ---: | ---: |
| total_cases | 40 | 40 |
| category_accuracy | 1.000 | 0.950 |
| priority_accuracy | 1.000 | 0.875 |
| priority_within_one_accuracy | 1.000 | 1.000 |
| routing_accuracy | 1.000 | 0.975 |
| human_review_precision | 1.000 | 0.909 |
| human_review_recall | 1.000 | 0.909 |
| human_review_f1 | 1.000 | 0.909 |
| critical_priority_recall | 1.000 | 0.917 |
| exact_match_accuracy | 1.000 | 0.750 |
| failures | 0 | 14 |

The rules baseline is perfect on the tuned original dataset. The LLM is weaker on this dataset across exact match, priority accuracy, human review metrics, and critical priority recall.

This does not mean the rules are broadly better. It means the original dataset is no longer an independent test of the tuned rules.

## Holdout Dataset Comparison

| Metric | Rules | LLM |
| --- | ---: | ---: |
| total_cases | 24 | 24 |
| category_accuracy | 0.750 | 0.958 |
| priority_accuracy | 0.750 | 0.667 |
| priority_within_one_accuracy | 0.875 | 0.958 |
| routing_accuracy | 0.667 | 0.917 |
| human_review_precision | 0.857 | 1.000 |
| human_review_recall | 0.545 | 0.818 |
| human_review_f1 | 0.667 | 0.900 |
| critical_priority_recall | 0.200 | 0.800 |
| exact_match_accuracy | 0.542 | 0.583 |
| failures | 11 | 13 |

On the holdout dataset, the LLM is slightly stronger than rules on exact match accuracy and much stronger on critical priority recall. It also performs better on category accuracy, routing accuracy, and human review metrics.

The LLM still has more failure records than the rules because failures include review-reason mismatches and other field-level mismatches, not only exact-match misses.

## Exact Match Accuracy

Exact match requires category, priority, routing target, and human-review decision to all match.

On the original dataset, rules score `1.000` and the LLM scores `0.750`. On the holdout dataset, rules score `0.542` and the LLM scores `0.583`.

The holdout result is more informative for generalization: the LLM is only slightly ahead on exact match, so it should not be treated as a complete replacement for deterministic policy logic.

## Critical Priority Recall

Critical priority recall measures whether expected `P0` and `P1` cases are predicted as `P0` or `P1`. This matters because missed high-priority tickets are riskier than many ordinary classification mistakes.

On the original dataset, rules score `1.000` and the LLM scores `0.917`. On the holdout dataset, rules drop to `0.200`, while the LLM scores `0.800`.

This is the clearest LLM advantage in the holdout run. The LLM appears better at recognizing high-impact wording that the deterministic rules did not cover.

## Human Review Metrics

On the original dataset, rules score `1.000` for human review precision, recall, and F1. The LLM scores `0.909` across all three.

On the holdout dataset, rules score `0.857` precision, `0.545` recall, and `0.667` F1. The LLM scores `1.000` precision, `0.818` recall, and `0.900` F1.

The holdout review metrics suggest the LLM is better at identifying cases that should be reviewed, while still avoiding false-positive review decisions in this run.

## Representative LLM Original Dataset Failures

### `billing_subscription_002`

Subject: Disputed charge may become chargeback

- expected priority: `P2`
- predicted priority: `P1`
- mismatched fields: `priority`, `review_reasons`

This is an over-escalation of a billing-sensitive case.

### `billing_subscription_004`

Subject: Need invoice copy and PO update

- expected requires_human_review: `false`
- predicted requires_human_review: `true`
- predicted review reason included `billing_sensitive`

This shows the LLM can over-apply billing-sensitive review logic to routine billing operations.

### `bug_report_003`

Subject: Regression after latest release

- expected priority: `P1`
- expected human review: `true`
- predicted priority: `P2`
- predicted human review: `false`

This is a missed high-priority bug case and is more concerning than a harmless over-escalation.

### `bug_report_004`

Subject: Button alignment looks off

- expected: `bug_report` routed to `engineering_triage`
- predicted: `feature_request` routed to `product_management`

This shows category confusion between cosmetic defects and product requests.

## Representative LLM Holdout Dataset Failures

### `account_access_holdout_002`

Subject: Invite link question

- expected: `account_access`, `P2`, `support_tier_1`
- predicted: `feature_request`, `P3`, `product_management`

This shows the LLM can misread an operational account-access request as a product request.

### `account_access_holdout_003`

Subject: Manager keeps seeing MFA prompt

- expected routing: `support_tier_1`
- predicted routing: `support_tier_2`

This is a routing over-escalation.

### `billing_subscription_holdout_001`

Subject: Invoice PDF button question

- expected priority: `P2`
- predicted priority: `P3`

This is a priority under-escalation for a routine billing support case.

### `billing_subscription_holdout_002`

Subject: Refund disputed renewal

- expected priority: `P2`
- predicted priority: `P1`
- predicted additional escalation reasons

This is another billing over-escalation pattern.

### `bug_report_holdout_001`

Subject: Dashboard totals changed

- expected priority: `P1`
- expected human review: `true`
- predicted priority: `P2`
- predicted human review: `false`

This is a missed high-priority product correctness issue.

## Where Rules Are Stronger

Rules are stronger on the tuned original dataset, where they reach perfect exact match and perfect human review metrics. They also behave predictably and are easy to inspect when a decision needs to be explained.

Rules are useful for deterministic safeguards, especially where policy should not depend on model interpretation.

## Where LLM Is Stronger

The LLM generalizes better on the holdout dataset for category selection, routing, human review, and critical priority recall.

The strongest signal is holdout critical priority recall: `0.800` for the LLM compared with `0.200` for rules. That suggests the LLM handles some high-impact wording that the rule keyword coverage misses.

## Remaining Weaknesses

Both approaches still miss important cases.

The rules baseline is brittle on holdout wording, especially indirect high-impact wording. The LLM still over-escalates some billing cases, under-escalates some bug cases, and confuses account-access or cosmetic-defect wording with feature requests.

Review-reason mismatches remain important because human review logic is part of the system output, not just a secondary explanation.

## Recommended Next Step

Use these results to design a small hybrid triage pass later. A reasonable direction is to keep deterministic safeguards for high-risk policy cases while using the LLM for natural-language classification and routing.

Hybrid logic is not implemented yet. The next implementation step should be planned separately and tested against both the original and holdout datasets.
