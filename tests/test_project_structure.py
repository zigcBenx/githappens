from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ProjectStructureTests(unittest.TestCase):
    def test_legacy_entrypoint_is_thin_wrapper(self):
        entrypoint = ROOT / "gitHappens.py"
        source = entrypoint.read_text(encoding="utf-8")

        self.assertIn("from githappens.main import main", source)
        self.assertIn('if __name__ == "__main__":', source)

    def test_modular_package_contains_expected_boundaries(self):
        expected_files = [
            "githappens/config.py",
            "githappens/gitlab_api.py",
            "githappens/git_utils.py",
            "githappens/interactive.py",
            "githappens/templates.py",
            "githappens/commands/create_issue.py",
            "githappens/commands/open_mr.py",
            "githappens/commands/review.py",
            "githappens/commands/report.py",
            "githappens/commands/deploy.py",
        ]

        for file_name in expected_files:
            self.assertTrue((ROOT / file_name).exists())


if __name__ == "__main__":
    unittest.main()
