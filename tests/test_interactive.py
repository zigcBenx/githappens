import sys
import types
import unittest
from unittest import mock

from githappens.interactive import select_template


class InteractiveTests(unittest.TestCase):
    def test_select_template_uses_lazy_inquirer_import(self):
        fake_inquirer = types.SimpleNamespace()
        fake_inquirer.List = lambda *args, **kwargs: ("list", args, kwargs)
        fake_inquirer.prompt = mock.Mock(return_value={"template": "Bug"})

        with mock.patch.dict(sys.modules, {"inquirer": fake_inquirer}):
            self.assertEqual(select_template(["Bug", "Custom"]), "Bug")

        fake_inquirer.prompt.assert_called_once()
