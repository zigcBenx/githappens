import io
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

import main


class MainTests(unittest.TestCase):
    def test_main_prints_help_without_loading_runtime(self):
        with patch("main.load_runtime") as load_runtime, redirect_stdout(io.StringIO()):
            result = main.main([])

        self.assertEqual(result, 1)
        load_runtime.assert_not_called()

    def test_ai_review_command_does_not_require_gitlab_config(self):
        with patch("ai_code_review.run_review") as run_review, patch("main.load_runtime") as load_runtime:
            result = main.main(["ai", "review"])

        self.assertEqual(result, 0)
        run_review.assert_called_once()
        load_runtime.assert_not_called()


if __name__ == "__main__":
    unittest.main()
