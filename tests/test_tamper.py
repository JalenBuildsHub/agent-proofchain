from proofchain.tamper import render_tamper_markdown, run_tamper_evaluation


def test_tamper_evaluation_reports_detectable_and_undetectable_cases():
    report = run_tamper_evaluation()
    assert report["scenario_count"] == 5
    assert report["all_expected_outcomes_matched"] is True

    scenarios = {item["id"]: item for item in report["scenarios"]}
    assert scenarios["payload-edit"]["actual_detected"] is True
    assert scenarios["previous-hash-edit"]["actual_detected"] is True
    assert scenarios["receipt-hash-edit"]["actual_detected"] is True
    assert scenarios["middle-row-deletion"]["actual_detected"] is True
    assert scenarios["final-row-truncation"]["actual_detected"] is False


def test_tamper_markdown_states_known_limitation():
    markdown = render_tamper_markdown(run_tamper_evaluation())
    assert "Known limitation" in markdown
    assert "external signed checkpoint" in markdown
