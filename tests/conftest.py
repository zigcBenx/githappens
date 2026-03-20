"""
Patch config file I/O before importing application modules that load config.py.
Tests must not require configs/config.ini or configs/templates.json on disk.
"""
import sys
import types

# Stub inquirer so modules that import it can load without the package installed.
if "inquirer" not in sys.modules:
    _inquirer_stub = types.ModuleType("inquirer")

    class _QuestionStub:
        def __init__(self, *args, **kwargs):
            pass

    _inquirer_stub.List = _QuestionStub
    _inquirer_stub.Text = _QuestionStub
    _inquirer_stub.Checkbox = _QuestionStub

    def _prompt_stub(_questions):
        return {}

    _inquirer_stub.prompt = _prompt_stub
    sys.modules["inquirer"] = _inquirer_stub

import builtins
import configparser
import io
import json

# Install patches at conftest import time (before test modules import gitlab_api, etc.)
_REAL_OPEN = builtins.open
_FAKE_TEMPLATES_PAYLOAD = {
    "templates": [
        {
            "name": "Bug",
            "labels": ["bug"],
            "type": "issue",
            "weight": 1,
            "estimated_time": None,
        },
    ],
    "reviewers": [101, 102],
    "productionMappings": {},
}


def _patched_configparser_read(self, filenames, encoding=None):
    fake_ini = """[DEFAULT]
base_url = https://gitlab.test
group_id = 99
custom_template = CustomTmpl
GITLAB_TOKEN = test-token
delete_branch_after_merge = false
squash_commits = false
production_pipeline_name = deploy
production_job_name =
production_ref =
"""
    self.read_string(fake_ini)
    if isinstance(filenames, str):
        return [filenames]
    return list(filenames)


def _patched_open(file, *args, **kwargs):
    path = file if isinstance(file, str) else str(file)
    if path.endswith("templates.json") or "templates.json" in path:
        return io.StringIO(json.dumps(_FAKE_TEMPLATES_PAYLOAD))
    return _REAL_OPEN(file, *args, **kwargs)


configparser.ConfigParser.read = _patched_configparser_read
builtins.open = _patched_open
