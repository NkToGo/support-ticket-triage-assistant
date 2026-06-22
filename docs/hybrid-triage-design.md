# Hybrid Triage Design

This document describes a possible future hybrid triage strategy for the AI Support Ticket Triage Assistant. It is a design note only. Hybrid triage is not implemented yet.

The design is based on the existing rules baseline, structured-output LLM path, labeled datasets, and the Rules vs LLM evaluation comparison.

## Why Consider Hybrid Triage

The current system has two independent triage paths:

- A deterministic rules baseline.
- A structured-output LLM triage path.

The comparison results show different strengths:

- Rules are perfect on the tuned original dataset.
- Rules drop on the holdout dataset, especially on critical priority recall.
- The LLM is weaker than rules on the tuned original dataset.
- The LLM is slightly stronger than rules on holdout exact match.
- The LLM is much stronger than rules on holdout critical priority recall.

This suggests that neither path should automatically replace the other. A conservative hybrid strategy may be useful because rules provide deterministic safeguards while the LLM handles varied wording and cases the rules do not cover.

## What Rules Do Well

The rules baseline is useful because it is deterministic, inspectable, and easy to test. It performs especially well on known patterns from the tuned original dataset.

Rules are a good fit for:

- Clear security, privacy, billing, incident, and access-blocking triggers.
- Policy-style human review requirements.
- Stable routing decisions for obvious categories.
- Repeatable behavior that can be explained without model interpretation.
- Guardrails where safety-sensitive decisions should not rely only on LLM judgment.

The main weakness is brittleness. Rules can miss indirect wording, mixed-intent tickets, and cases that use language not covered by keyword or phrase groups.

## What The LLM Does Well

The LLM path is useful because it can interpret more varied natural language while still returning the existing structured `TriageResult` schema.

The holdout results show stronger behavior on:

- Category selection.
- Routing accuracy.
- Human review recall and F1.
- Critical priority recall.
- Tickets whose wording does not match existing rule phrases.

The LLM still makes meaningful mistakes. It can over-escalate billing cases, under-escalate some bug reports, and confuse account-access or cosmetic-defect wording with feature requests.

## Why Holdout Results Matter

The original dataset was used during rules tuning. A perfect score on that dataset is useful as a regression check, but it is not an independent measure of generalization.

The holdout dataset is more useful for judging behavior on new wording and stress cases. It shows where the rules are brittle and where the LLM generalizes better. Future hybrid evaluation should treat holdout behavior as the stronger signal for practical robustness.

## Critical Priority Recall

Critical priority recall measures whether expected `P0` and `P1` cases are predicted as `P0` or `P1`.

This is a major safety signal because missed high-priority tickets are riskier than ordinary classification mistakes. A false low-priority decision can delay incident response, security review, or handling for a blocked customer.

The Rules vs LLM comparison showed a large holdout gap on this metric. Rules scored lower on holdout critical priority recall, while the LLM caught more high-priority cases. A hybrid design should preserve deterministic safeguards while using the LLM to reduce missed critical cases.

## Why Human Review Remains Important

Human review is part of the triage decision, not a fallback after failure. It is required when a decision is high-risk, ambiguous, policy-sensitive, or likely to affect a customer relationship.

A hybrid system should require human review for:

- `P0` or `P1` priority.
- Security, privacy, compliance, suspicious access, data deletion, or possible data exposure.
- Refunds, disputed charges, chargebacks, cancellations, credits, or other billing-sensitive requests.
- Outage, downtime, severe latency, or broad-impact incident signals.
- Customer escalation, legal action, churn risk, or executive visibility.
- Missing critical details or meaningful disagreement between rules and LLM.

Human review should not be removed for sensitive cases even if both systems are confident.

## Conservative V1 Strategy

A conservative v1 hybrid flow should run rules first.

The system can accept the rules result when:

- Rules confidence is high.
- The category is not `other_unclear`.
- The ticket does not appear mixed-intent.
- There is no safety-sensitive ambiguity.
- There is no need for an additional LLM interpretation.

The system should call the LLM when:

- Rules confidence is low.
- Rules classify the ticket as `other_unclear`.
- Multiple concrete categories appear plausible.
- The ticket has mixed intent.
- The ticket includes indirect high-impact wording that rules may miss.

The final output should still be structured triage only. The system should never auto-resolve tickets and should not generate customer-facing replies.

Human review should always be required for high-risk or sensitive cases, regardless of which path produced the final label.

## Possible Decision Modes

Future implementation could expose a selected strategy value for evaluation and debugging.

| Mode | Meaning |
| --- | --- |
| `rules_only` | Use only the deterministic rules result. |
| `llm_only` | Use only the LLM result. |
| `rules_then_llm_for_uncertain` | Run rules first and call the LLM only when rules are unclear, low-confidence, or mixed-intent. |
| `rules_with_llm_review_for_sensitive_cases` | Run rules first and call the LLM as a second opinion for sensitive, high-risk, or policy-relevant cases. |

The initial hybrid implementation should prefer a small number of modes and make the selected mode visible in evaluation output.

## Future Hybrid Output

If hybrid triage is implemented later, it may need a wrapper around the existing `TriageResult` rather than changing the existing schema.

A future hybrid result could include:

- Final triage result.
- Selected strategy.
- Rules prediction.
- Optional LLM prediction.
- Decision rationale.
- Whether human review is required.
- Disagreement fields between rules and LLM.

The final triage decision should remain compatible with the existing `TriageResult` fields so current API and evaluation behavior can continue to work.

## Future Evaluation Plan

A later hybrid implementation should be evaluated against the same datasets used for rules and LLM evaluation.

The evaluation should compare:

- Rules vs LLM vs hybrid on the original dataset.
- Rules vs LLM vs hybrid on the holdout dataset.

Metrics should include:

- Exact match accuracy.
- Category accuracy.
- Priority accuracy.
- Routing accuracy.
- Human review precision, recall, and F1.
- Critical priority recall.
- Rules and LLM disagreement cases.

Failure analysis should include:

- Missed `P0` and `P1` cases.
- Missed human review triggers.
- False-positive review load.
- Routing mistakes.
- Priority over-escalation and under-escalation.
- Cases where rules and LLM disagree.
- Cases where labels may be ambiguous.

The hybrid path should be judged primarily on holdout behavior and safety-sensitive recall, not only tuned-dataset exact match.

## Non-Goals

This design does not include:

- Autonomous ticket resolution.
- Customer-facing reply generation.
- Retrieval or RAG.
- Vector database usage.
- Frontend work.
- Production readiness claims.
- Replacing human review for sensitive cases.

The goal is a small, testable hybrid decision policy for structured triage, not a full support automation system.
