import unittest
from unittest import mock

from githappens import git_utils


class GitUtilsTest(unittest.TestCase):
    def test_get_project_link_returns_origin_url(self):
        completed = mock.Mock(returncode=0, stdout=b"git@gitlab.com:group/project.git\n")

        with mock.patch("subprocess.run", return_value=completed):
            self.assertEqual(
                git_utils.get_project_link_from_current_dir(),
                "git@gitlab.com:group/project.git",
            )

    def test_get_project_link_returns_minus_one_when_not_git_repo(self):
        completed = mock.Mock(returncode=1, stdout=b"")

        with mock.patch("subprocess.run", return_value=completed):
            self.assertEqual(git_utils.get_project_link_from_current_dir(), -1)


if __name__ == "__main__":
    unittest.main()
