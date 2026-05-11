import unittest
from unittest.mock import patch

import interactive


class FakeInquirer:
    class List:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class Text:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    class Checkbox:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    def __init__(self, answer):
        self.answer = answer

    def prompt(self, _questions):
        return self.answer


class InteractiveTests(unittest.TestCase):
    def test_select_template_returns_prompted_template(self):
        fake = FakeInquirer({"template": "Bug"})
        with patch("interactive._inquirer", return_value=fake):
            selected = interactive.select_template([{"name": "Bug"}], "Custom")

        self.assertEqual(selected, "Bug")

    def test_prompt_spent_time_returns_prompted_minutes(self):
        fake = FakeInquirer({"spent_time": "45"})
        with patch("interactive._inquirer", return_value=fake):
            self.assertEqual(interactive.prompt_spent_time(), "45")


if __name__ == "__main__":
    unittest.main()
