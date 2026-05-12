import unittest
from unittest.mock import patch

import interactive


class FakePrompt:
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

    @staticmethod
    def prompt(_questions):
        return {"selected_reviewers": ["1", "2"]}


class InteractiveTests(unittest.TestCase):
    def test_choose_reviewers_manually_uses_user_display_names(self):
        users = {
            1: {"name": "Ada Lovelace", "username": "ada"},
            2: {"name": "Grace Hopper", "username": "grace"},
        }

        with patch.object(interactive, "inquirer", FakePrompt):
            selected = interactive.choose_reviewers_manually(
                reviewers=[1, 2],
                get_user=lambda reviewer_id: users[reviewer_id],
            )

        self.assertEqual(selected, [1, 2])


if __name__ == "__main__":
    unittest.main()
