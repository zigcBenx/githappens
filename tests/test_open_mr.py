import unittest

from githappens.commands import open_mr


class OpenMergeRequestTest(unittest.TestCase):
    def test_project_path_from_ssh_remote(self):
        self.assertEqual(
            open_mr.project_path_from_remote("git@gitlab.com:group/project.git"),
            "group/project",
        )

    def test_project_path_from_https_remote(self):
        self.assertEqual(
            open_mr.project_path_from_remote("https://gitlab.com/group/project.git"),
            "group/project",
        )

    def test_project_path_from_unknown_remote(self):
        self.assertIsNone(open_mr.project_path_from_remote("not-a-remote"))


if __name__ == "__main__":
    unittest.main()
