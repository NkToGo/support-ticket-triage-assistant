# Rules vs LLM vs Hybrid Evaluation Comparison

Date: 2026-06-25

## Purpose

This report compares three triage paths:

- deterministic rules triage
- structured-output LLM triage
- conservative hybrid triage

The results are based on synthetic labeled datasets. They are useful for engineering comparison inside this project, but they are not broad reliability or production-readiness claims.

## Dataset Overview

| Dataset | File | Cases | Notes |
| --- | --- | ---: | --- |
| Original | `data/eval/triage_cases.json` | 40 | Used during rules tuning. Useful as a regression check, but not an independent generalization signal. |
| Holdout | `data/eval/triage_holdout_cases.json` | 24 | Separate stress dataset. More useful for checking generalization to varied wording. |

Holdout results matter more than tuned original dataset results because the original dataset has already shaped the rules baseline.

## Original Dataset

Commands:

```powershell
py scripts/run_triage_eval.py --mode rules
py scripts/run_triage_eval.py --mode llm
py scripts/run_triage_eval.py --mode hybrid
```

| Metric | Rules | LLM | Hybrid |
| --- | ---: | ---: | ---: |
| total_cases | 40 | 40 | 40 |
| category_accuracy | 1.000 | 0.950 | 1.000 |
| priority_accuracy | 1.000 | 0.875 | 0.975 |
| priority_within_one_accuracy | 1.000 | 1.000 | 1.000 |
| routing_accuracy | 1.000 | 0.975 | 1.000 |
| human_review_precision | 1.000 | 0.909 | 1.000 |
| human_review_recall | 1.000 | 0.909 | 1.000 |
| human_review_f1 | 1.000 | 0.909 | 1.000 |
| critical_priority_recall | 1.000 | 0.917 | 1.000 |
| exact_match_accuracy | 1.000 | 0.750 | 0.975 |
| hybrid_used_llm_count | not applicable | not applicable | 22 |
| hybrid_rules_only_count | not applicable | not applicable | 18 |
| hybrid_disagreement_case_count | not applicable | not applicable | 10 |
| failures | 0 | 14 | 5 |

The rules baseline remains strongest on the tuned original dataset. Hybrid stays close to rules while calling the LLM on 22 of 40 cases. The LLM alone is weaker on this dataset, especially on exact match.

## Holdout Dataset

Commands:

```powershell
py scripts/run_triage_eval.py --mode rules --dataset data/eval/triage_holdout_cases.json
py scripts/run_triage_eval.py --mode llm --dataset data/eval/triage_holdout_cases.json
py scripts/run_triage_eval.py --mode hybrid --dataset data/eval/triage_holdout_cases.json
```

| Metric | Rules | LLM | Hybrid |
| --- | ---: | ---: | ---: |
| total_cases | 24 | 24 | 24 |
| category_accuracy | 0.750 | 0.958 | 0.875 |
| priority_accuracy | 0.750 | 0.667 | 0.792 |
| priority_within_one_accuracy | 0.875 | 0.958 | 0.958 |
| routing_accuracy | 0.667 | 0.917 | 0.792 |
| human_review_precision | 0.857 | 1.000 | 0.900 |
| human_review_recall | 0.545 | 0.818 | 0.818 |
| human_review_f1 | 0.667 | 0.900 | 0.857 |
| critical_priority_recall | 0.200 | 0.800 | 0.600 |
| exact_match_accuracy | 0.542 | 0.583 | 0.667 |
| hybrid_used_llm_count | not applicable | not applicable | 12 |
| hybrid_rules_only_count | not applicable | not applicable | 12 |
| hybrid_disagreement_case_count | not applicable | not applicable | 11 |
| failures | 11 | 13 | 10 |

On the holdout dataset, hybrid has the strongest exact match accuracy and the fewest failures among the three paths. It does not lead every metric: the LLM has higher category accuracy, routing accuracy, human review F1, and critical priority recall.

## Interpretation

Rules are cheap, deterministic, and strong on known patterns. They are easy to inspect and are useful for policy-style safeguards, but the holdout result shows that keyword coverage is brittle.

The LLM handles varied wording and some holdout cases better. It is stronger than rules on holdout category accuracy, routing accuracy, human review recall, and critical priority recall. It also makes its own mistakes, including over-escalation and category confusion.

Hybrid v1 keeps deterministic safeguards and calls the LLM selectively. On holdout, it improves exact match over both rules and LLM, but it is not automatically best on every metric. This is expected for a conservative hybrid strategy.

The holdout dataset is the more important comparison point because it was not used for rules tuning. The original dataset remains useful as a regression check.

## Safety And Human Review

Human review precision, recall, and F1 are important because the system is not meant to auto-resolve tickets. It produces structured triage decisions and identifies when a human should review the result.

On the holdout dataset, rules have low human review recall at `0.545`, while LLM and hybrid both reach `0.818`. Hybrid improves substantially over rules but still misses some review-needed cases.

Critical priority recall is a major safety signal. Missing expected `P0` or `P1` cases is higher risk than over-escalating a few lower-priority cases because a missed critical ticket can delay incident response, security review, or support for a blocked customer.

On holdout critical priority recall, rules score `0.200`, LLM scores `0.800`, and hybrid scores `0.600`. Hybrid improves over rules but does not match the LLM on this metric. Sensitive and high-risk cases should continue to require human review.

## Failure Patterns

Remaining holdout issues include:

- Account access routing and priority misses, especially when access impact is indirect.
- Billing review-reason differences and sensitivity decisions.
- Bug vs technical support confusion, especially around API and product-behavior wording.
- Critical priority recall below perfect, meaning some high-priority cases are still under-detected.

These failures suggest that hybrid v1 is useful, but the decision thresholds and disagreement handling need more evaluation.

## Engineering Conclusion

Hybrid v1 is a useful comparison path because it shows the tradeoff between deterministic safeguards and LLM-assisted interpretation. It improves holdout exact match and failure count without requiring the LLM on every case.

The next work should focus on:

- stronger hybrid decision thresholds
- better disagreement analysis
- a larger evaluation set
- possible hybrid evaluation reporting from the CLI later
- avoiding overfitting to the holdout set

No production-readiness claim should be made from these results. The datasets are synthetic and intentionally small.
