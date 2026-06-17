from types import SimpleNamespace
from typing import Any

import pytest

from support_triage import llm
from support_triage.models import (
    CustomerTier,
    ReviewReason,
    RoutingTarget,
    TicketCategory,
    TicketInput,
    TicketPriority,
    TriageResult,
)


class FakeResponses:
    def __init__(self, parsed: Any) -> None:
        self.parsed = parsed
        self.calls: list[dict[str, Any]] = []

    def parse(self, **kwargs: Any) -> SimpleNamespace:
        self.calls.append(kwargs)
        return SimpleNamespace(output_parsed=self.parsed)


class FakeClient:
    def __init__(self, parsed: Any) -> None:
        self.responses = FakeResponses(parsed)


def test_prompt_messages_include_taxonomy_and_ticket_fields() -> None:
    ticket = TicketInput(
        subject="Cannot export reports",
        body="The CSV export fails with a 502 error.",
        customer_tier=CustomerTier.PREMIUM,
        product_area="reports",
    )

    messages = llm.build_triage_messages(ticket)
    rendered = "\n".join(message["content"] for message in messages)

    assert "account_access" in rendered
    assert "billing_subscription" in rendered
    assert "P0" in rendered
    assert "support_tier_1" in rendered
    assert "low_confidence" in rendered
    assert "Cannot export reports" in rendered
    assert "The CSV export fails with a 502 error." in rendered
    assert "premium" in rendered
    assert "reports" in rendered


def test_missing_api_key_raises_clear_runtime_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    with pytest.raises(llm.LLMTriageConfigurationError, match="OPENAI_API_KEY"):
        llm.triage_with_llm(
            TicketInput(subject="Need help", body="Please look at this issue.")
        )


def test_triage_with_llm_returns_parsed_triage_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = TriageResult(
        category=TicketCategory.DATA_SECURITY_PRIVACY,
        priority=TicketPriority.P1,
        routing_target=RoutingTarget.SECURITY_COMPLIANCE,
        requires_human_review=True,
        review_reasons=[
            ReviewReason.PRIORITY_HIGH,
            ReviewReason.SECURITY_OR_PRIVACY,
        ],
        confidence=0.86,
        rationale="Detected suspicious account access with security risk.",
    )
    fake_client = FakeClient(expected)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_MODEL", "test-model")
    monkeypatch.setenv("OPENAI_TRIAGE_TEMPERATURE", "0")
    monkeypatch.setattr(llm, "_create_openai_client", lambda api_key: fake_client)

    result = llm.triage_with_llm(
        TicketInput(
            subject="Suspicious access",
            body="A disabled contractor account can still open reports.",
        )
    )

    assert result == expected
    assert fake_client.responses.calls[0]["model"] == "test-model"
    assert fake_client.responses.calls[0]["text_format"] is TriageResult
    assert fake_client.responses.calls[0]["temperature"] == 0.0


def test_triage_with_llm_validates_parsed_dict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parsed = {
        "category": "feature_request",
        "priority": "P3",
        "routing_target": "product_management",
        "requires_human_review": False,
        "review_reasons": [],
        "confidence": 0.78,
        "rationale": "Detected a product enhancement request.",
    }
    fake_client = FakeClient(parsed)
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delenv("OPENAI_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_TRIAGE_TEMPERATURE", raising=False)
    monkeypatch.setattr(llm, "_create_openai_client", lambda api_key: fake_client)

    result = llm.triage_with_llm(
        TicketInput(
            subject="Add dashboard themes",
            body="We would like more color customization options.",
        )
    )

    assert result.category == TicketCategory.FEATURE_REQUEST
    assert result.priority == TicketPriority.P3
    assert result.routing_target == RoutingTarget.PRODUCT_MANAGEMENT
    assert result.requires_human_review is False
    assert fake_client.responses.calls[0]["model"] == llm.DEFAULT_OPENAI_MODEL
