from fastapi.testclient import TestClient

from support_triage.main import app


def test_post_triage_rules_returns_valid_triage_json() -> None:
    client = TestClient(app)

    response = client.post(
        "/triage/rules",
        json={
            "subject": "Cannot sign in",
            "body": "I am locked out after MFA reset.",
            "customer_tier": "enterprise",
            "product_area": "authentication",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "category": "account_access",
        "priority": "P1",
        "routing_target": "support_tier_2",
        "requires_human_review": True,
        "review_reasons": ["priority_high"],
        "confidence": 0.85,
        "rationale": "Detected account access and blocked-login signals.",
    }


def test_post_triage_llm_missing_api_key_returns_503(
    monkeypatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = TestClient(app)

    response = client.post(
        "/triage/llm",
        json={
            "subject": "Cannot sign in",
            "body": "I am locked out after MFA reset.",
            "customer_tier": "enterprise",
            "product_area": "authentication",
        },
    )

    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_post_triage_hybrid_rules_only_without_api_key(
    monkeypatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = TestClient(app)

    response = client.post(
        "/triage/hybrid",
        json={
            "subject": "Feature request",
            "body": "Would like dark mode added to the admin dashboard.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["strategy"] == "rules_only"
    assert body["used_llm"] is False
    assert body["llm_result"] is None
    assert body["final_result"]["category"] == "feature_request"


def test_post_triage_hybrid_missing_api_key_returns_503_when_llm_needed(
    monkeypatch,
) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    client = TestClient(app)

    response = client.post(
        "/triage/hybrid",
        json={
            "subject": "Need help",
            "body": "Call me back.",
        },
    )

    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]
