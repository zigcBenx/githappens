import pytest

import gitHappens


def test_main_without_args_prints_help_and_exits():
    with pytest.raises(SystemExit) as error:
        gitHappens.main([])

    assert error.value.code == 1


def test_summary_command_dispatches(monkeypatch):
    called = {"summary": False}

    def fake_summary():
        called["summary"] = True

    monkeypatch.setattr(gitHappens, "get_two_weeks_commits", fake_summary)

    gitHappens.main(["summary"])

    assert called["summary"] is True
