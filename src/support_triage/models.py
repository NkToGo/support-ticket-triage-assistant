from enum import StrEnum

from pydantic import BaseModel, Field


class TicketCategory(StrEnum):
    ACCOUNT_ACCESS = "account_access"
    BILLING_SUBSCRIPTION = "billing_subscription"
    BUG_REPORT = "bug_report"
    PERFORMANCE_AVAILABILITY = "performance_availability"
    TECHNICAL_SUPPORT = "technical_support"
    DATA_SECURITY_PRIVACY = "data_security_privacy"
    FEATURE_REQUEST = "feature_request"
    OTHER_UNCLEAR = "other_unclear"


class TicketPriority(StrEnum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class RoutingTarget(StrEnum):
    SUPPORT_TIER_1 = "support_tier_1"
    SUPPORT_TIER_2 = "support_tier_2"
    ENGINEERING_TRIAGE = "engineering_triage"
    INCIDENT_RESPONSE = "incident_response"
    BILLING_OPS = "billing_ops"
    SECURITY_COMPLIANCE = "security_compliance"
    PRODUCT_MANAGEMENT = "product_management"
    CUSTOMER_SUCCESS = "customer_success"


class ReviewReason(StrEnum):
    LOW_CONFIDENCE = "low_confidence"
    AMBIGUOUS_CATEGORY = "ambiguous_category"
    PRIORITY_HIGH = "priority_high"
    SECURITY_OR_PRIVACY = "security_or_privacy"
    BILLING_SENSITIVE = "billing_sensitive"
    POTENTIAL_INCIDENT = "potential_incident"
    CUSTOMER_ESCALATION = "customer_escalation"
    MISSING_CRITICAL_DETAILS = "missing_critical_details"
    POLICY_SENSITIVE = "policy_sensitive"


class CustomerTier(StrEnum):
    FREE = "free"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class TicketInput(BaseModel):
    subject: str = Field(min_length=1)
    body: str = Field(min_length=1)
    customer_tier: CustomerTier | None = None
    product_area: str | None = None


class TriageResult(BaseModel):
    category: TicketCategory
    priority: TicketPriority
    routing_target: RoutingTarget
    requires_human_review: bool
    review_reasons: list[ReviewReason]
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str = Field(min_length=1)
