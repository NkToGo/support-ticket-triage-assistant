# AI Support Ticket Triage Assistant - Project Scope

## Project Goal

The AI Support Ticket Triage Assistant is a backend-first Applied AI learning and engineering project that classifies incoming support tickets, estimates priority, recommends a routing target, and decides whether a human should review the result before action is taken.

The project is intended to demonstrate structured AI decision support for support operations. It is not a customer-facing chatbot and it is not another retrieval-augmented generation assistant.

The core output of the system will be a structured triage decision, for example:

```json
{
  "category": "account_access",
  "priority": "P1",
  "routing_target": "support_tier_2",
  "requires_human_review": true,
  "review_reasons": ["priority_high"],
  "confidence": 0.82,
  "rationale": "The customer cannot sign in after an MFA reset and is blocked from work."
}
```

## What V1 Will Do

V1 will focus on a narrow, testable triage workflow:

- Accept a support ticket subject and body, with optional lightweight metadata such as customer tier or reported product area.
- Classify the ticket into a predefined support taxonomy.
- Assign a priority using the ticket content and simple business rules.
- Recommend a routing target such as Tier 1 Support, Tier 2 Support, Billing, Security, Engineering Triage, or Product.
- Produce structured output that can be validated against a schema.
- Include a concise rationale for the decision.
- Flag tickets for human review when the decision is high-risk, ambiguous, low-confidence, or policy-sensitive.
- Compare a simple rules-based baseline, an LLM-based classifier, and a hybrid approach.
- Include an evaluation dataset, metrics, and failure analysis notes.

The initial implementation should be easy to run locally and easy to evaluate. A command-line or small backend module is enough for v1; a frontend is not required.

## What V1 Will Not Do

V1 will intentionally avoid broad product scope:

- It will not answer customer questions using a knowledge base.
- It will not use RAG, semantic search, citations, or retrieval ranking.
- It will not automatically send replies to customers.
- It will not create, close, merge, or update real support tickets in external systems.
- It will not integrate with Zendesk, Jira, Slack, email, or CRM systems.
- It will not train or fine-tune a model.
- It will not claim production readiness, SLA compliance, full security review, or live operational reliability.
- It will not attempt to handle every support domain, attachment type, language, or escalation workflow.
- It will not start with a React frontend.

These exclusions keep the project focused on triage quality, structured outputs, and evaluation rather than surface area.

## Why This Complements The Previous RAG Project

The previous IT Helpdesk Knowledge Assistant demonstrated retrieval-heavy capabilities: RAG, semantic search, citations, fallback behavior, answer evaluation, and a React user interface.

This project demonstrates a different Applied AI pattern:

- Classification instead of retrieval.
- Structured outputs instead of natural-language answers.
- Priority and routing policy instead of citation-backed response generation.
- Human-in-the-loop review logic instead of direct assistant answers.
- Error analysis around operational decisions instead of answer faithfulness.

Together, the two projects cover complementary AI system patterns: one system helps users find answers, while this system helps an operations team make consistent intake decisions.

## Planned High-Level Architecture

V1 should be designed around small, testable components:

1. **Ticket input**
   - Load sample tickets from local fixtures or receive a ticket object from a simple function or CLI.

2. **Triage schema**
   - Define the required structured output fields, allowed categories, priority levels, routing targets, confidence, rationale, and review reasons.

3. **Rules baseline**
   - Implement simple deterministic rules for obvious cases such as security incidents, billing disputes, outages, password reset issues, and feature requests.

4. **LLM triage**
   - Use a prompt and schema-constrained output to classify, prioritize, route, and explain the ticket.

5. **Hybrid decision policy**
   - Combine deterministic safeguards with the LLM result. For example, security-related tickets or P0/P1 tickets can always require human review even when the model is confident.

6. **Human review gate**
   - Convert confidence, category, priority, ambiguity, and policy-sensitive signals into a clear review decision.

7. **Evaluation harness**
   - Run labeled examples through the baseline, LLM, and hybrid approaches.
   - Report category, priority, routing, review-trigger, and schema-validity metrics.
   - Capture representative failure cases for analysis.

The architecture should remain backend-first. A small API can be added later if it helps demonstrate the workflow, but it should come after the taxonomy and evaluation loop are useful.

## Applied AI Engineering Goals

This project is meant to practice and document practical AI engineering judgment:

- Clear problem framing and scoped v1 delivery.
- Schema-first use of LLMs for operational workflows.
- Evaluation before UI polish.
- Baseline comparison rather than assuming the LLM is better.
- Human review logic for risky or uncertain decisions.
- Honest documentation of limitations and failure modes.
- Maintainable backend design without premature infrastructure.

The goal is not to make the assistant appear perfect. The goal is to build a system with clear boundaries, measurable behavior, and a realistic path for improving triage quality over time.
