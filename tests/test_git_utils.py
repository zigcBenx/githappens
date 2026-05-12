import subprocess
from types import SimpleNamespace

import git_utils


def test_get_project_link_from_current_dir_returns_remote(monkeypatch):
    def fake_run(command, stdout, stderr):
        assert command == ["git", "remote", "get-url", "origin"]
        return SimpleNamespace(returncode=0, stdout=b"git@gitlab.com:group/project.git\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert git_utils.getProjectLinkFromCurrentDir() == "git@gitlab.com:group/project.git"


def test_get_project_link_from_current_dir_returns_minus_one_when_git_fails(monkeypatch):
    def fake_run(command, stdout, stderr):
        return SimpleNamespace(returncode=1, stdout=b"")

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert git_utils.getProjectLinkFromCurrentDir() == -1
