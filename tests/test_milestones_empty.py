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
    config_path = config_dir / "config.ini"
    templates_path = config_dir / "templates.json"
    previous_config = config_path.read_text(encoding="utf-8") if config_path.exists() else None
    previous_templates = templates_path.read_text(encoding="utf-8") if templates_path.exists() else None

    config_path.write_text(
        "[DEFAULT]\n"
        "base_url=https://gitlab.example\n"
        "group_id=42\n"
        "custom_template=Custom\n"
        "GITLAB_TOKEN=test-token\n"
        "squash_commits=true\n"
        "delete_branch_after_merge=true\n",
        encoding="utf-8",
    )
    templates_path.write_text(
        '{"templates": [], "reviewers": []}',
        encoding="utf-8",
    )

    inquirer_stub = types.SimpleNamespace(
        prompt=mock.Mock(),
        Text=lambda *args, **kwargs: ("Text", args, kwargs),
        List=lambda *args, **kwargs: ("List", args, kwargs),
        Checkbox=lambda *args, **kwargs: ("Checkbox", args, kwargs),
    )

    try:
        with mock.patch.dict(sys.modules, {"inquirer": inquirer_stub}):
            spec = importlib.util.spec_from_file_location("gitHappens_under_test", root / "gitHappens.py")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    finally:
        if previous_config is None:
            config_path.unlink(missing_ok=True)
        else:
            config_path.write_text(previous_config, encoding="utf-8")
        if previous_templates is None:
            templates_path.unlink(missing_ok=True)
        else:
            templates_path.write_text(previous_templates, encoding="utf-8")


class EmptyMilestonesTest(unittest.TestCase):
    def test_current_milestone_returns_none_when_no_active_milestone_exists(self):
        git_happens = load_githappens_module()
        result = mock.Mock()
        result.stdout = json.dumps([
            {"id": 1, "title": "Past", "start_date": "2024-01-01", "due_date": "2024-01-31"},
            {"id": 2, "title": "Future", "start_date": "2099-01-01", "due_date": "2099-01-31"},
        ]).encode()

        with mock.patch.object(git_happens.subprocess, "run", return_value=result):
            milestone = git_happens.list_milestones(current=True)

        self.assertIsNone(milestone)

    def test_missing_current_milestone_omits_milestone_id(self):
        git_happens = load_githappens_module()

        with mock.patch.object(git_happens, "get_milestone", return_value=None):
            milestone_id = git_happens.get_milestone_id(manual=False)

        self.assertFalse(milestone_id)


if __name__ == "__main__":
    unittest.main()
