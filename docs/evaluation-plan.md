# Evaluation Plan

This project should be evaluation-first. The assistant is useful only if its structured triage decisions can be measured, compared against baselines, and improved through failure analysis.

The initial evaluation does not need to be large. A small, carefully labeled dataset is more valuable than a large set of vague examples.

## What Will Be Evaluated

V1 should evaluate the full triage decision, not only category classification:

- **Category selection:** Did the assistant choose the correct primary ticket category?
- **Priority assignment:** Did the assistant assign the correct priority level?
- **Routing target:** Did the assistant send the ticket to the correct team?
- **Human review decision:** Did the assistant correctly identify tickets that require review?
- **Review reasons:** Were the review triggers appropriate and specific?
- **Structured output validity:** Did the assistant return valid output matching the expected schema?
- **Rationale quality:** Does the rationale cite the relevant ticket facts without inventing details?

Rationale quality can start as a lightweight manual review. It does not need a complicated automated score in v1.

## Systems To Compare

V1 should compare at least three approaches.

### 1. Rules Baseline

A deterministic baseline using keywords, simple pattern matching, and policy rules.

Expected strengths:

- Easy to understand.
- Strong on obvious billing, security, outage, and feature-request cases.
- Useful as a minimum-quality comparison.

Expected weaknesses:

- Brittle wording coverage.
- Poor handling of nuanced or multi-intent tickets.
- Limited ability to explain ambiguous decisions.

### 2. LLM Triage

An LLM prompt that receives the ticket, taxonomy, and output schema, then returns one structured triage decision.

Expected strengths:

- Better handling of natural language variation.
- Better rationale generation.
- Better handling of context that is not captured by simple keywords.

Expected weaknesses:

- Possible overconfidence.
- Possible schema errors without strict validation.
- May under-trigger human review unless prompted and measured carefully.

### 3. Hybrid Triage

A combined approach where deterministic policy guards and schema validation wrap the LLM decision.

Example hybrid rules:

- Always require human review for `P0` and `P1`.
- Always require human review for security, privacy, compliance, refund, cancellation, or suspected incident cases.
- Let deterministic rules override routing for obvious security, billing, and incident tickets.
- Use the LLM for nuanced classification, rationale, and ambiguous cases.
- Force `other_unclear` plus human review when required fields or details are missing.

Expected strengths:

- More reliable handling of high-risk cases.
- Better review recall than a pure LLM.
- More realistic applied AI workflow.

Expected weaknesses:

- More policy complexity.
- Possible false-positive human review volume.
- Requires careful failure analysis to avoid rule sprawl.

## Metrics

The evaluation report should include:

| Metric | Purpose |
| --- | --- |
| Category accuracy | Overall primary-category correctness. |
| Category macro F1 | Performance across categories, including smaller classes. |
| Priority accuracy | Exact priority match rate. |
| Priority within-one accuracy | Whether predicted priority is at most one level away from the label. |
| Critical priority recall | Recall for `P0` and `P1`, because missing high-priority tickets is costly. |
| Routing accuracy | Correct routing target match rate. |
| Human review precision | How often review flags are actually needed. |
| Human review recall | How often required reviews are caught. This should be prioritized over precision for high-risk cases. |
| Schema validity rate | Percentage of outputs that pass structured validation. |
| Invalid output count | Number and type of malformed or incomplete outputs. |
| Confidence calibration notes | Whether high-confidence predictions are usually correct, reviewed with simple buckets. |

For v1, cost and latency can be recorded as rough observations, but they should not dominate the evaluation unless they expose a clear tradeoff.

## Initial Eval Dataset

Start with a labeled local dataset of approximately 40 to 80 tickets. The examples can be synthetic but should be realistic, varied, and written in customer language.

The dataset should include:

- At least 5 examples per category.
- A mix of `P0`, `P1`, `P2`, and `P3`.
- Ambiguous tickets that could fit more than one category.
- Tickets with emotional urgency but low actual impact.
- Tickets with understated wording but high actual impact.
- Tickets requiring human review.
- Tickets that should not require human review.
- A few unclear or incomplete tickets.

Labels should include expected category, priority, routing target, review decision, and review reasons.

## Example Eval Cases

| Case | Expected Category | Expected Priority | Expected Route | Human Review |
| --- | --- | --- | --- | --- |
| "Our entire team cannot access the app. The login page returns 503 for everyone." | `performance_availability` | `P0` | `incident_response` | Yes |
| "URGENT: I want dark mode in the dashboard." | `feature_request` | `P3` | `product_management` | No |
| "We need a refund for a duplicate charge on invoice INV-1042." | `billing_subscription` | `P2` | `billing_ops` | Yes |
| "A former employee can still open reports after their account was disabled." | `data_security_privacy` | `P1` | `security_compliance` | Yes |
| "CSV export fails with error 502 after the latest release." | `bug_report` | `P2` | `engineering_triage` | No |
| "Can someone help me set up SAML SSO for our workspace?" | `technical_support` | `P2` | `support_tier_2` | No |
| "I cannot get into my account because MFA is going to a lost phone." | `account_access` | `P1` | `support_tier_2` | Yes |
| "The admin page is a little slow sometimes, but everything works." | `performance_availability` | `P3` | `support_tier_1` | No |
| "Please delete all data for user jane@example.com under GDPR." | `data_security_privacy` | `P1` | `security_compliance` | Yes |
| "Need help. Call me back." | `other_unclear` | `P3` | `support_tier_1` | Yes |

## Failure Analysis

Failure analysis should be written after each evaluation run. It should explain what failed, why it likely failed, and what change should be tested next.

Each failure analysis pass should include:

- Confusion patterns between categories.
- Priority mistakes, especially missed `P0` or `P1` cases.
- Routing mistakes that would send work to the wrong team.
- Missed human review triggers.
- False-positive human review triggers that could create avoidable queue volume.
- Invalid or incomplete structured outputs.
- Rationale issues, including invented facts or rationales that ignore key ticket details.
- Cases where labels may be ambiguous or need revision.
- Whether the baseline, LLM, or hybrid approach handled the case best.

The goal is not to hide failures. The goal is to make the system's behavior visible enough to improve it.

## Reporting Format

Each evaluation run should produce a short report with:

- Dataset version or file name.
- System version being evaluated.
- Metric table.
- Top failure categories.
- Representative failure examples.
- Planned next changes.

The report should be honest about limitations. A v1 learning project can use disciplined engineering practices without claiming enterprise-grade automation.
