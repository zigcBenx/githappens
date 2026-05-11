import unittest
import io
from contextlib import redirect_stdout
from subprocess import CalledProcessError
from unittest import mock

from githappens.git_utils import (
    build_branch_name,
    build_merge_request_url,
    find_matching_project_id,
    get_project_search_term,
)


class GitUtilsTests(unittest.TestCase):
    def test_build_branch_name_normalizes_title(self):
        self.assertEqual(
            build_branch_name(116, "Refactor monolithic gitHappens.py into modular architecture"),
            "116-refactor-monolithic-githappens.py-into-modular-architecture",
        )

    def test_build_branch_name_preserves_legacy_slash_and_underscore_behavior(self):
        self.assertEqual(
            build_branch_name(123, "Fix API/client_v2 path"),
            "123-fix-api/client_v2-path",
        )

    def test_get_project_search_term_strips_git_suffix(self):
        self.assertEqual(
            get_project_search_term("https://gitlab.example.com/team/repo.git"),
            "repo",
        )

    def test_find_matching_project_id_matches_ssh_remote(self):
        projects = [
            {
                "id": 7,
                "ssh_url_to_repo": "git@gitlab.example.com:team/repo.git",
                "http_url_to_repo": "https://gitlab.example.com/team/repo.git",
                "path_with_namespace": "team/repo",
            }
        ]
        self.assertEqual(
            find_matching_project_id(projects, "git@gitlab.example.com:team/repo.git"),
            7,
        )

    def test_build_merge_request_url_handles_http_and_ssh_remotes(self):
        self.assertEqual(
            build_merge_request_url(
                "https://gitlab.example.com",
                "https://gitlab.example.com/team/repo.git",
                42,
            ),
            "https://gitlab.example.com/team/repo/-/merge_requests/42",
        )
        self.assertEqual(
            build_merge_request_url(
                "https://gitlab.example.com",
                "git@gitlab.example.com:team/repo.git",
                42,
            ),
            "https://gitlab.example.com/team/repo/-/merge_requests/42",
        )

    def test_get_two_weeks_commits_returns_empty_string_on_git_error(self):
        from githappens.git_utils import get_two_weeks_commits

        with mock.patch("subprocess.check_output", side_effect=CalledProcessError(128, "git")):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(get_two_weeks_commits(), "")

    def test_get_two_weeks_commits_returns_empty_string_when_git_missing(self):
        from githappens.git_utils import get_two_weeks_commits

        with mock.patch("subprocess.check_output", side_effect=FileNotFoundError):
            with redirect_stdout(io.StringIO()):
                self.assertEqual(get_two_weeks_commits(), "")
