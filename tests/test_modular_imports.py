import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _write_test_configs():
    config_dir = Path(__file__).resolve().parents[1] / "configs"
    config_dir.mkdir(exist_ok=True)
    (config_dir / "config.ini").write_text(
        "[DEFAULT]\n"
        "base_url = https://gitlab.example.com\n"
        "group_id = 1\n"
        "custom_template = Custom\n"
        "GITLAB_TOKEN = dummy\n"
        "delete_branch_after_merge = false\n"
        "squash_commits = false\n"
    )
    (config_dir / "templates.json").write_text('{"templates": [], "reviewers": []}')


def test_entrypoint_exports_main():
    _write_test_configs()
    module = importlib.import_module("main")
    assert callable(module.main)


def test_focused_modules_import():
    _write_test_configs()
    for name in [
        "config",
        "gitlab_api",
        "git_utils",
        "templates",
        "interactive",
        "commands.create_issue",
        "commands.review",
        "commands.deploy",
        "commands.report",
        "commands.summary",
    ]:
        importlib.import_module(name)
