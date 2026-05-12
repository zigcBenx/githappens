from commands import summary


def test_generate_smart_summary_returns_without_commits(monkeypatch):
    called = {"value": False}

    def fake_get_two_weeks_commits(return_output=False):
        called["value"] = return_output
        return ""

    monkeypatch.setattr(summary, "get_two_weeks_commits", fake_get_two_weeks_commits)

    assert summary.generate_smart_summary() is None
    assert called["value"] is True
