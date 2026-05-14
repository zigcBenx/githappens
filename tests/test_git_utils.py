import unittest
from unittest import mock

import git_utils


class GitUtilsTest(unittest.TestCase):
    def test_get_project_link_returns_origin_url(self):
        completed = mock.Mock(returncode=0, stdout=b"git@gitlab.com:group/project.git\n")
        with mock.patch("subprocess.run", return_value=completed):
            self.assertEqual(
                git_utils.getProjectLinkFromCurrentDir(),
                "git@gitlab.com:group/project.git",
            )

    def test_get_project_link_returns_negative_on_failure(self):
        completed = mock.Mock(returncode=1, stdout=b"", stderr=b"error")
        with mock.patch("subprocess.run", return_value=completed):
            self.assertEqual(git_utils.getProjectLinkFromCurrentDir(), -1)

    def test_get_current_branch(self):
        with mock.patch(
            "subprocess.check_output", return_value="feature-branch\n"
        ) as co:
            result = git_utils.getCurrentBranch()
            self.assertEqual(result, "feature-branch")
            co.assert_called_once_with(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True
            )


if __name__ == "__main__":
    unittest.main()
