#!/usr/bin/env python3
"""Backward compatibility shim. Implementations live in commands.ai_review."""
from commands.ai_review import (
    Colors,
    SYSTEM_PROMPT,
    display_review_results,
    format_gitlab_comment,
    get_branch_diff,
    get_diff_refs,
    get_merge_request_changes,
    get_openai_client,
    post_inline_comment,
    post_to_merge_request,
    print_issues,
    review_code,
    run_review,
    run_review_for_mr,
)

if __name__ == '__main__':
    run_review()
