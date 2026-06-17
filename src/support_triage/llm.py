import json
import os
from enum import StrEnum
from typing import Any

from support_triage.models import (
    CustomerTier,
    ReviewReason,
    RoutingTarget,
    TicketCategory,
    TicketInput,
    TicketPriority,
    TriageResult,
)


DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
DEFAULT_TEMPERATURE = 0.0


class LLMTriageConfigurationError(RuntimeError):
    """Raised when LLM triage is called without required configuration."""


def triage_with_llm(ticket: TicketInput) -> TriageResult:
    api_key = _require_api_key()
    client = _create_openai_client(api_key)
    messages = build_triage_messages(ticket)

    response = client.responses.parse(
        model=_get_model_name(),
        input=messages,
        text_format=TriageResult,
        temperature=_get_temperature(),
    )

    return _coerce_triage_result(response.output_parsed)


def build_triage_messages(ticket: TicketInput) -> list[dict[str, str]]:
    ticket_payload = ticket.model_dump(mode="json")
    return [
        {"role": "system", "content": _system_prompt()},
        {
            "role": "user",
            "content": "Triage this support ticket:\n"
            + json.dumps(ticket_payload, indent=2, sort_keys=True),
        },
    ]


def _system_prompt() -> str:
    return f"""You classify support tickets for internal triage.

Return exactly one structured triage result matching the provided schema. Do not write a customer-facing response.

Allowed ticket categories: {_enum_values(TicketCategory)}.
Allowed priorities: {_enum_values(TicketPriority)}.
Allowed routing targets: {_enum_values(RoutingTarget)}.
Allowed human review reasons: {_enum_values(ReviewReason)}.
Allowed customer tiers: {_enum_values(CustomerTier)}.

Category guidance:
- account_access: login, password, MFA, 2FA, SSO, locked-out, invite, or account access issues.
- billing_subscription: invoice, charge, refund, renewal, cancellation, payment, plan, or subscription issues.
- bug_report: broken, incorrect, reproducible, regressed, or erroring product behavior.
- performance_availability: outage, downtime, slowness, latency, timeout, unavailable service, or broad service impact.
- technical_support: setup, configuration, API key, webhook, permissions, import, export, or integration troubleshooting that is not clearly a bug.
- data_security_privacy: security, privacy, compliance, suspicious access, data deletion, data exposure, or sensitive data handling.
- feature_request: product enhancement, missing capability, usability suggestion, or workflow improvement.
- other_unclear: vague, insufficient, unrelated, or unsupported requests.

Priority guidance:
- P0: widespread outage, active security incident, data exposure, data loss, or many users blocked from core functionality.
- P1: blocked core workflow, access blocked, possible security/privacy risk, high-value customer impact, or explicit escalation with real impact.
- P2: normal bugs, configuration/support issues, billing requests, or single-user problems.
- P3: feature requests, cosmetic or low-impact issues, and unclear low-evidence tickets.

Routing guidance:
- account_access routes to support_tier_2 when access is blocked, otherwise support_tier_1.
- billing_subscription routes to billing_ops.
- bug_report routes to engineering_triage.
- performance_availability routes to incident_response for P0/P1, otherwise support_tier_1.
- technical_support routes to support_tier_2.
- data_security_privacy routes to security_compliance.
- feature_request routes to product_management.
- other_unclear routes to support_tier_1.

Human review guidance:
- Require review for confidence below 0.75.
- Require review for P0 or P1.
- Require review for security, privacy, compliance, deletion, suspicious access, or possible data exposure.
- Require review for refunds, credits, cancellations, disputed charges, chargebacks, or other billing-sensitive requests.
- Require review for outage, downtime, severe latency, or broad-impact incident signals.
- Require review for escalation, legal action, churn risk, executive visibility, or missing critical details.
- Use policy_sensitive for requests requiring policy judgment, data deletion, data exposure, or access-control-sensitive handling.

Set confidence from 0.0 to 1.0. Keep rationale to one short sentence grounded only in the ticket facts."""


def _enum_values(enum_type: type[StrEnum]) -> str:
    return ", ".join(item.value for item in enum_type)


def _require_api_key() -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise LLMTriageConfigurationError(
            "LLM triage requires OPENAI_API_KEY to be set."
        )
    return api_key


def _create_openai_client(api_key: str) -> Any:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise LLMTriageConfigurationError(
            "LLM triage requires the OpenAI Python package. Install project dependencies first."
        ) from exc

    return OpenAI(api_key=api_key)


def _get_model_name() -> str:
    return os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL)


def _get_temperature() -> float:
    raw_value = os.getenv("OPENAI_TRIAGE_TEMPERATURE")
    if raw_value is None:
        return DEFAULT_TEMPERATURE

    try:
        return float(raw_value)
    except ValueError as exc:
        raise LLMTriageConfigurationError(
            "OPENAI_TRIAGE_TEMPERATURE must be a numeric value."
        ) from exc


def _coerce_triage_result(parsed: Any) -> TriageResult:
    if parsed is None:
        raise RuntimeError("OpenAI structured output did not include a parsed result.")
    if isinstance(parsed, TriageResult):
        return parsed
    return TriageResult.model_validate(parsed)
