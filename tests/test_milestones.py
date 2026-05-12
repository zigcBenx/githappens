import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


def load_githappens_module():
    root = Path(__file__).resolve().parents[1]
    config_dir = root / "configs"
    config_dir.mkdir(exist_ok=True)
    (config_dir / "config.ini").write_text(
        "[DEFAULT]\n"
        "base_url=https://gitlab.example\n"
        "group_id=42\n"
        "custom_template=Custom\n"
        "GITLAB_TOKEN=test-token\n"
        "squash_commits=true\n"
        "delete_branch_after_merge=true\n",
        encoding="utf-8",
    )
    (config_dir / "templates.json").write_text(
        '{"templates": [], "reviewers": []}',
        encoding="utf-8",
    )

    inquirer_stub = types.SimpleNamespace(
        prompt=mock.Mock(),
        Text=lambda *args, **kwargs: ("Text", args, kwargs),
        List=lambda *args, **kwargs: ("List", args, kwargs),
        Checkbox=lambda *args, **kwargs: ("Checkbox", args, kwargs),
    )
    sys.modules["inquirer"] = inquirer_stub

    spec = importlib.util.spec_from_file_location("gitHappens_under_test", root / "gitHappens.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class MilestoneSearchTest(unittest.TestCase):
    def test_list_milestones_sends_search_query_to_gitlab(self):
        git_happens = load_githappens_module()
        result = mock.Mock()
        result.stdout = json.dumps([{"id": 7, "title": "Release 1"}]).encode()

        with mock.patch.object(git_happens.subprocess, "run", return_value=result) as run:
            milestones = git_happens.list_milestones(search="Release 1")

        self.assertEqual(milestones, [{"id": 7, "title": "Release 1"}])
        command = run.call_args.args[0]
        self.assertEqual(command[0:2], ["glab", "api"])
        self.assertIn("search=Release%201", command[2])

    def test_manual_milestone_search_falls_back_to_active_list_when_no_match(self):
        git_happens = load_githappens_module()

        with mock.patch.object(git_happens, "list_milestones", side_effect=[[], [{"id": 3, "title": "Fallback"}]]) as list_milestones, \
             mock.patch.object(git_happens, "select_milestone", return_value="Fallback"):
            git_happens.inquirer.prompt.return_value = {"milestone_search": "wrong"}

            milestone = git_happens.get_milestone(True)

        self.assertEqual(milestone, {"id": 3, "title": "Fallback"})
        list_milestones.assert_has_calls([
            mock.call(search="wrong"),
            mock.call(),
        ])


if __name__ == "__main__":
    unittest.main()
