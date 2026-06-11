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
