import json
import unittest
from unittest import mock

import ai_code_review


class DocumentationSuggestionTest(unittest.TestCase):
    def test_format_documentation_comment_returns_none_without_suggestions(self):
        result = ai_code_review.format_documentation_comment({
            "needed": False,
            "summary": "No docs needed",
            "suggestions": [],
        })

        self.assertIsNone(result)

    def test_format_documentation_comment_includes_summary_and_suggestions(self):
        result = ai_code_review.format_documentation_comment({
            "needed": True,
            "summary": "The CLI behavior changed.",
            "suggestions": [
                {
                    "file": "README.md",
                    "reason": "New flag added",
                    "suggestion": "Document the --select flag in the review section.",
                }
            ],
        })

        self.assertIn("## Documentation Suggestions", result)
        self.assertIn("The CLI behavior changed.", result)
        self.assertIn("README.md", result)
        self.assertIn("Document the --select flag", result)

    def test_format_documentation_comment_keeps_summary_without_suggestions(self):
        result = ai_code_review.format_documentation_comment({
            "needed": True,
            "summary": "Docs should mention that review can post multiple comments.",
            "suggestions": [],
        })

        self.assertIn("## Documentation Suggestions", result)
        self.assertIn("Docs should mention that review can post multiple comments.", result)
        self.assertIn("Review the diff and update documentation as needed.", result)

    def test_suggest_documentation_updates_uses_diff_content(self):
        fake_openai = mock.Mock()
        fake_openai.chat.completions.create.return_value.choices = [
            mock.Mock(message=mock.Mock(content=json.dumps({
                "needed": True,
                "summary": "Docs should mention behavior.",
                "suggestions": [],
            })))
        ]

        with mock.patch("ai_code_review.get_openai_client", return_value=fake_openai):
            result = ai_code_review.suggest_documentation_updates("diff --git a/file.py b/file.py")

        self.assertTrue(result["needed"])
        call_kwargs = fake_openai.chat.completions.create.call_args.kwargs
        self.assertIn("Documentation", call_kwargs["messages"][0]["content"])
        self.assertIn("diff --git", call_kwargs["messages"][1]["content"])

    def test_run_review_for_mr_posts_documentation_when_diff_refs_missing(self):
        review_results = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "summary": "No code issues.",
        }
        documentation_results = {
            "needed": True,
            "summary": "Docs should mention behavior.",
            "suggestions": [
                {
                    "file": "README.md",
                    "reason": "New command behavior",
                    "suggestion": "Document the behavior.",
                }
            ],
        }

        with mock.patch("ai_code_review.get_branch_diff", return_value="diff"), \
             mock.patch("ai_code_review.review_code", return_value=review_results), \
             mock.patch("ai_code_review.suggest_documentation_updates", return_value=documentation_results), \
             mock.patch("ai_code_review.get_diff_refs", return_value=None), \
             mock.patch("ai_code_review.post_to_merge_request") as post_comment:
            ai_code_review.run_review_for_mr(1, 2, "token", "https://gitlab.example/api/v4")

        self.assertEqual(post_comment.call_count, 2)
        posted_bodies = [call.args[0] for call in post_comment.call_args_list]
        self.assertTrue(any("Documentation Suggestions" in body for body in posted_bodies))


if __name__ == "__main__":
    unittest.main()
