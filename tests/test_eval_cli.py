import sys

from scripts import run_triage_eval
from support_triage.evaluation import EvaluationSummary


def test_cli_accepts_hybrid_mode_with_monkeypatched_evaluator(
    monkeypatch,
    capsys,
) -> None:
    def fake_evaluate_hybrid(*, dataset_path=None, limit=None):
        assert dataset_path == "fake.json"
        assert limit == 2
        return EvaluationSummary(
            dataset_path="fake.json",
            total_cases=2,
            category_accuracy=1.0,
            priority_accuracy=1.0,
            priority_within_one_accuracy=1.0,
            routing_accuracy=1.0,
            human_review_precision=1.0,
            human_review_recall=1.0,
            human_review_f1=1.0,
            critical_priority_recall=1.0,
            exact_match_accuracy=1.0,
            failures=[],
            hybrid_used_llm_count=1,
            hybrid_rules_only_count=1,
            hybrid_disagreement_case_count=1,
        )

    monkeypatch.setattr(run_triage_eval, "evaluate_hybrid", fake_evaluate_hybrid)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "run_triage_eval.py",
            "--mode",
            "hybrid",
            "--dataset",
            "fake.json",
            "--limit",
            "2",
        ],
    )

    exit_code = run_triage_eval.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "mode: hybrid" in output
    assert "dataset: fake.json" in output
    assert "limit: 2" in output
    assert "hybrid_used_llm_count: 1" in output
