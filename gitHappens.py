#!/usr/bin/env python3
"""GitHappens CLI tool - backward-compatible entry point.

This file is kept as a thin wrapper so existing user aliases
(e.g., alias gh='python3 .../gitHappens.py') continue to work.

All implementation has been moved to focused modules:
  - config.py, templates.py
  - gitlab_api.py, git_utils.py, interactive.py
  - commands/create_issue.py, commands/open_mr.py
  - commands/review.py, commands/deploy.py, commands/summary.py
  - main.py (entry point)
"""
from main import main

if __name__ == '__main__':
    main()
