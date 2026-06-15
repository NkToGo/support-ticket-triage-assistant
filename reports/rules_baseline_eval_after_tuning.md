# Rules Baseline Evaluation After Tuning

Date: 2026-06-15

Command:

```powershell
py scripts/run_triage_eval.py --mode rules
```

The original baseline report is preserved at `reports/rules_baseline_eval.md` for comparison.

## Headline Metrics

| Metric | Before tuning | After tuning |
| --- | ---: | ---: |
| total_cases | 40 | 40 |
| category_accuracy | 0.775 | 1.000 |
| priority_accuracy | 0.675 | 1.000 |
| priority_within_one_accuracy | 0.925 | 1.000 |
| routing_accuracy | 0.775 | 1.000 |
| human_review_precision | 0.692 | 1.000 |
| human_review_recall | 0.818 | 1.000 |
| human_review_f1 | 0.750 | 1.000 |
| critical_priority_recall | 1.000 | 1.000 |
| exact_match_accuracy | 0.525 | 1.000 |
| failures | 23 | 0 |

## What Improved

Category and routing accuracy improved after narrowing broad keyword matches and adding targeted disambiguation for UI, billing, technical support, feature request, performance, and security/privacy language.

Priority accuracy improved after removing customer tier as a standalone high-priority trigger and adding more specific high-impact bug, low-impact performance, and data exposure rules.

Human review precision improved after reducing false-positive review triggers for ordinary billing, bug, feature request, performance, and support tickets.

Human review recall and critical priority recall are both 1.000 on this dataset. The tuned baseline still catches the labeled high-priority and review-required cases in the current eval set.

Exact match accuracy improved from 0.525 to 1.000 because the tuned rules now match category, priority, routing target, and human-review decision for every current labeled case.

## What Got Worse

No tracked metric got worse on the current 40-case dataset.

This does not mean the rules are generally complete. The dataset is small and synthetic, and the tuned baseline should still be treated as a deterministic baseline rather than a robust production triage system.

## Remaining Failure Patterns

The current eval run has zero recorded failures, so there are no remaining failures within this dataset.

Residual risks still remain:

- New wording may still cause keyword collisions.
- Multi-intent tickets may need more nuanced uncertainty handling.
- Priority rules may still be brittle outside the current examples.
- Review reason labels may drift as the taxonomy evolves.
- The current dataset is not large enough to prove broad coverage.

## Notes On The Tuning Pass

The tuning pass was intentionally small. It focused on the failure patterns from the original report:

- Separated ordinary billing language from billing-sensitive actions.
- Reduced priority over-escalation from customer tier alone.
- Improved handling for cosmetic UI bugs and feature requests.
- Added targeted security/privacy and data exposure signals.
- Improved low-impact performance handling.
- Improved vague and missing-detail detection.

The result should be used as the next deterministic comparison point for future evaluation work.
