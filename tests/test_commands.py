import unittest
from unittest.mock import patch

from commands.create_issue import start_issue_creation


class CommandTests(unittest.TestCase):
    @patch("commands.create_issue.create_merge_request")
    @patch("commands.create_issue.create_branch")
    @patch("commands.create_issue.create_issue")
    @patch("commands.create_issue.prompt_estimated_time", return_value="30")
    def test_start_issue_creation_only_issue_skips_branch_and_mr(
        self,
        _prompt,
        create_issue,
        create_branch,
        create_merge_request,
    ):
        create_issue.return_value = {"iid": 1, "title": "Test"}

        result = start_issue_creation(
            project_id=1,
            title="Test",
            milestone=False,
            epic=False,
            iteration=False,
            selected_settings={"labels": ["Bug"]},
            only_issue=True,
        )

        self.assertEqual(result, {"iid": 1, "title": "Test"})
        create_issue.assert_called_once()
        create_branch.assert_not_called()
        create_merge_request.assert_not_called()

    @patch("commands.create_issue.create_merge_request")
    @patch("commands.create_issue.create_branch")
    @patch("commands.create_issue.create_issue")
    @patch("commands.create_issue.prompt_estimated_time", return_value="60")
    def test_start_issue_creation_splits_estimate_for_multiple_projects(
        self,
        _prompt,
        create_issue,
        create_branch,
        create_merge_request,
    ):
        create_issue.return_value = {"iid": 2, "title": "Test"}
        create_branch.return_value = {"name": "branch"}
        create_merge_request.return_value = {"iid": 3, "title": "Test", "source_branch": "branch"}
        settings = {"labels": ["Bug"]}

        start_issue_creation(
            project_id=[1, 2],
            title="Test",
            milestone=False,
            epic=False,
            iteration=False,
            selected_settings=settings,
            only_issue=False,
        )

        create_issue.assert_called_once_with(
            "Test",
            [1, 2],
            False,
            False,
            False,
            {"labels": ["Bug"], "estimated_time": 30},
        )
        self.assertEqual(settings, {"labels": ["Bug"]})


if __name__ == "__main__":
    unittest.main()
