# Triage Taxonomy

This document defines the initial support ticket taxonomy for v1. The taxonomy should stay small enough to evaluate reliably while still covering common support operations.

The triage assistant should return one primary category, one priority, one routing target, and zero or more human review reasons.

## Ticket Categories

| Category | Description | Common Signals |
| --- | --- | --- |
| `account_access` | The customer cannot sign in, reset credentials, pass MFA, access an account, or use SSO. | login failed, password reset, MFA, 2FA, locked out, SSO, invite expired |
| `billing_subscription` | Billing, invoices, plan changes, renewals, refunds, cancellations, payment failures, or subscription confusion. | invoice, charge, refund, cancel, renewal, credit card, plan, subscription |
| `bug_report` | The customer reports product behavior that appears broken, incorrect, or reproducible. | error, broken, stopped working, expected vs actual, reproduce, regression |
| `performance_availability` | The customer reports downtime, degraded availability, latency, timeouts, or broad service impact. | outage, down, slow, timeout, unavailable, latency, all users affected |
| `technical_support` | Setup, configuration, integration, permissions, imports, exports, or troubleshooting that does not clearly indicate a product defect. | configure, setup, integration, API key, webhook, permissions, import, export |
| `data_security_privacy` | Security, privacy, compliance, data exposure, deletion requests, suspicious access, or sensitive data handling. | breach, leaked, GDPR, delete data, suspicious login, security, compliance |
| `feature_request` | Product enhancement requests, workflow improvements, missing capabilities, or usability suggestions. | feature request, can you add, improvement, would like, enhancement |
| `other_unclear` | The ticket is too vague, unrelated, spam-like, or does not fit the supported taxonomy. | unclear request, missing details, unrelated message, insufficient context |

## Priority Levels

| Priority | Meaning | Typical Criteria |
| --- | --- | --- |
| `P0` | Critical | Widespread outage, active security incident, data loss, severe availability issue, or many customers blocked from core functionality. |
| `P1` | High | A customer is blocked from a core workflow, an enterprise or high-value account has a severe issue, payment or access is blocking business, or there is possible security/privacy risk. |
| `P2` | Normal | A single user or team has a problem with a workaround, a normal bug report, a configuration issue, or a non-urgent billing/support request. |
| `P3` | Low | Feature request, cosmetic issue, general question, low-impact inconvenience, or unclear request that does not indicate urgency. |

Priority should be based on impact and urgency, not only emotional language. Words like "urgent" or "ASAP" are useful signals, but they should not automatically create `P0` without evidence of critical impact.

## Routing Targets

| Routing Target | Use When |
| --- | --- |
| `support_tier_1` | General support, common how-to questions, basic account questions, low-risk intake, or unclear tickets needing clarification. |
| `support_tier_2` | Complex troubleshooting, account access blocks, permissions issues, integrations, or tickets needing deeper support investigation. |
| `engineering_triage` | Reproducible bugs, suspected regressions, data integrity problems, or issues likely requiring product engineering review. |
| `incident_response` | Outages, widespread availability issues, severe degradation, or customer reports that may indicate an active incident. |
| `billing_ops` | Invoices, refunds, payments, renewals, cancellations, subscription changes, or account credit questions. |
| `security_compliance` | Security incidents, privacy requests, compliance concerns, suspicious access, or sensitive data exposure. |
| `product_management` | Feature requests, product feedback, prioritization input, or workflow enhancement suggestions. |
| `customer_success` | Adoption blockers, enterprise escalations, onboarding risk, relationship-sensitive requests, or non-technical account concerns. |

## Human Review Triggers

The assistant should require human review when any of these triggers apply:

| Review Reason | Trigger |
| --- | --- |
| `low_confidence` | The model confidence is below the chosen threshold, initially expected around 0.75. |
| `ambiguous_category` | The ticket plausibly fits multiple categories and the decision could affect routing. |
| `priority_high` | The selected priority is `P0` or `P1`. |
| `security_or_privacy` | The ticket involves security, privacy, compliance, suspicious access, deletion, or possible data exposure. |
| `billing_sensitive` | The ticket asks for refunds, credits, cancellation, disputed charges, or payment changes. |
| `potential_incident` | The ticket reports outage, downtime, severe latency, or many affected users. |
| `customer_escalation` | The customer mentions escalation, executive visibility, legal action, churn risk, or a high-value account. |
| `missing_critical_details` | The ticket lacks enough detail to route safely or assign a reliable priority. |
| `policy_sensitive` | The ticket requests action that may require company policy judgment, such as account deletion or access to another user's data. |

Human review does not mean the assistant failed. It means the assistant recognized that the decision should not be fully automated.

## Example Tickets

| Example | Expected Category | Expected Priority | Expected Route | Review? |
| --- | --- | --- | --- | --- |
| "I cannot log in after resetting MFA. Password works, but the app keeps asking for a code I do not have. I am blocked from accessing my dashboard." | `account_access` | `P1` | `support_tier_2` | Yes: `priority_high` |
| "A new employee never received their invite email. Can you resend it?" | `account_access` | `P2` | `support_tier_1` | No |
| "We were charged twice for our annual renewal. Please refund the duplicate payment." | `billing_subscription` | `P2` | `billing_ops` | Yes: `billing_sensitive` |
| "Can you cancel our trial before it converts next week?" | `billing_subscription` | `P2` | `billing_ops` | Yes: `billing_sensitive` |
| "When I click Export CSV, the download fails with error 502. It started after yesterday's release and happens every time." | `bug_report` | `P2` | `engineering_triage` | No |
| "The totals in the monthly report are wrong for all projects. Finance is using this report today." | `bug_report` | `P1` | `engineering_triage` | Yes: `priority_high` |
| "The application is down for our whole team. Nobody can load the login page." | `performance_availability` | `P0` | `incident_response` | Yes: `priority_high`, `potential_incident` |
| "Pages are taking 20 seconds to load for the last hour, and our whole support team is affected." | `performance_availability` | `P1` | `incident_response` | Yes: `priority_high`, `potential_incident` |
| "How do I configure the webhook signing secret for our staging environment?" | `technical_support` | `P2` | `support_tier_2` | No |
| "Our import from Salesforce fails because one field mapping is rejected. I am not sure which permission is missing." | `technical_support` | `P2` | `support_tier_2` | No |
| "A user who left the company still appears to have access. Please investigate immediately." | `data_security_privacy` | `P1` | `security_compliance` | Yes: `security_or_privacy`, `priority_high` |
| "Please delete all personal data for this user under GDPR." | `data_security_privacy` | `P1` | `security_compliance` | Yes: `security_or_privacy`, `policy_sensitive` |
| "It would be helpful if dashboards could be scheduled as weekly email reports." | `feature_request` | `P3` | `product_management` | No |
| "Can you add dark mode to the admin console?" | `feature_request` | `P3` | `product_management` | No |
| "Hello, I need help with my account. Please call me." | `other_unclear` | `P3` | `support_tier_1` | Yes: `missing_critical_details` |
| "Your website is bad." | `other_unclear` | `P3` | `support_tier_1` | Yes: `missing_critical_details` |

## Notes For V1

- Each ticket should receive one primary category even when secondary categories are present.
- Ambiguous tickets should be flagged for review rather than forced into overconfident automation.
- The taxonomy should change only when evaluation failures show a repeated gap.
- New categories should not be added for one-off edge cases unless they improve measurable routing quality.
