from support_triage.llm import triage_with_llm
from support_triage.models import (
    HybridStrategy,
    HybridTriageResult,
    ReviewReason,
    TicketCategory,
    TicketInput,
    TicketPriority,
    TriageResult,
)
from support_triage.rules import triage_with_rules


LLM_CONFIDENCE_THRESHOLD = 0.75
UNCERTAIN_REVIEW_REASONS = {
    ReviewReason.AMBIGUOUS_CATEGORY,
    ReviewReason.MISSING_CRITICAL_DETAILS,
}
SENSITIVE_REVIEW_REASONS = {
    ReviewReason.SECURITY_OR_PRIVACY,
    ReviewReason.BILLING_SENSITIVE,
    ReviewReason.POLICY_SENSITIVE,
    ReviewReason.POTENTIAL_INCIDENT,
    ReviewReason.CUSTOMER_ESCALATION,
}
LLM_TRIGGER_REVIEW_REASONS = UNCERTAIN_REVIEW_REASONS | SENSITIVE_REVIEW_REASONS
HIGH_PRIORITY_VALUES = {TicketPriority.P0, TicketPriority.P1}
PRIORITY_RISK_ORDER = {
    TicketPriority.P0: 0,
    TicketPriority.P1: 1,
    TicketPriority.P2: 2,
    TicketPriority.P3: 3,
}


def triage_with_hybrid(ticket: TicketInput) -> HybridTriageResult:
    rules_result = triage_with_rules(ticket)
    strategy = _select_strategy(rules_result)

    if strategy == HybridStrategy.RULES_ONLY:
        return HybridTriageResult(
            final_result=rules_result,
            strategy=strategy,
            rules_result=rules_result,
            llm_result=None,
            used_llm=False,
            disagreement_fields=[],
            decision_rationale="Rules result accepted; no LLM review trigger was present.",
        )

    llm_result = triage_with_llm(ticket)
    disagreement_fields = _disagreement_fields(rules_result, llm_result)
    final_result = _merge_results(rules_result, llm_result)

    return HybridTriageResult(
        final_result=final_result,
        strategy=strategy,
        rules_result=rules_result,
        llm_result=llm_result,
        used_llm=True,
        disagreement_fields=disagreement_fields,
        decision_rationale=_decision_rationale(strategy, disagreement_fields),
    )


def _select_strategy(result: TriageResult) -> HybridStrategy:
    if not _needs_llm(result):
        return HybridStrategy.RULES_ONLY
    if _has_sensitive_trigger(result):
        return HybridStrategy.RULES_WITH_LLM_REVIEW_FOR_SENSITIVE_CASES
    return HybridStrategy.RULES_THEN_LLM_FOR_UNCERTAIN


def _needs_llm(result: TriageResult) -> bool:
    return (
        result.confidence < LLM_CONFIDENCE_THRESHOLD
        or result.category == TicketCategory.OTHER_UNCLEAR
        or result.priority in HIGH_PRIORITY_VALUES
        or bool(set(result.review_reasons) & LLM_TRIGGER_REVIEW_REASONS)
    )


def _has_sensitive_trigger(result: TriageResult) -> bool:
    return (
        result.priority in HIGH_PRIORITY_VALUES
        or bool(set(result.review_reasons) & SENSITIVE_REVIEW_REASONS)
    )


def _disagreement_fields(
    rules_result: TriageResult,
    llm_result: TriageResult,
) -> list[str]:
    fields: list[str] = []
    if rules_result.category != llm_result.category:
        fields.append("category")
    if rules_result.priority != llm_result.priority:
        fields.append("priority")
    if rules_result.routing_target != llm_result.routing_target:
        fields.append("routing_target")
    if rules_result.requires_human_review != llm_result.requires_human_review:
        fields.append("requires_human_review")
    if set(rules_result.review_reasons) != set(llm_result.review_reasons):
        fields.append("review_reasons")
    return fields


def _merge_results(rules_result: TriageResult, llm_result: TriageResult) -> TriageResult:
    base_result = llm_result if _should_use_llm_base(rules_result, llm_result) else rules_result
    final_priority = _higher_risk_priority(rules_result.priority, llm_result.priority)
    review_reasons = _combined_review_reasons(
        rules_result.review_reasons,
        llm_result.review_reasons,
        final_priority,
    )

    return TriageResult(
        category=base_result.category,
        priority=final_priority,
        routing_target=base_result.routing_target,
        requires_human_review=(
            rules_result.requires_human_review
            or llm_result.requires_human_review
            or final_priority in HIGH_PRIORITY_VALUES
        ),
        review_reasons=review_reasons,
        confidence=base_result.confidence,
        rationale=_final_rationale(base_result, rules_result),
    )


def _should_use_llm_base(rules_result: TriageResult, llm_result: TriageResult) -> bool:
    rules_uncertain = (
        rules_result.confidence < LLM_CONFIDENCE_THRESHOLD
        or rules_result.category == TicketCategory.OTHER_UNCLEAR
        or bool(set(rules_result.review_reasons) & UNCERTAIN_REVIEW_REASONS)
    )
    llm_concrete = llm_result.category != TicketCategory.OTHER_UNCLEAR
    return rules_uncertain and llm_concrete


def _higher_risk_priority(
    first_priority: TicketPriority,
    second_priority: TicketPriority,
) -> TicketPriority:
    if PRIORITY_RISK_ORDER[first_priority] <= PRIORITY_RISK_ORDER[second_priority]:
        return first_priority
    return second_priority


def _combined_review_reasons(
    rules_reasons: list[ReviewReason],
    llm_reasons: list[ReviewReason],
    final_priority: TicketPriority,
) -> list[ReviewReason]:
    selected_reasons = set(rules_reasons) | set(llm_reasons)
    if final_priority in HIGH_PRIORITY_VALUES:
        selected_reasons.add(ReviewReason.PRIORITY_HIGH)
    return [reason for reason in ReviewReason if reason in selected_reasons]


def _final_rationale(base_result: TriageResult, rules_result: TriageResult) -> str:
    if base_result is rules_result:
        return "Hybrid kept the rules decision and applied conservative review safeguards."
    return "Hybrid used the LLM decision for an uncertain rules result and applied conservative safeguards."


def _decision_rationale(
    strategy: HybridStrategy,
    disagreement_fields: list[str],
) -> str:
    if not disagreement_fields:
        return f"Hybrid used {strategy.value}; rules and LLM agreed on compared fields."
    return (
        f"Hybrid used {strategy.value}; disagreements found in "
        f"{', '.join(disagreement_fields)}."
    )
