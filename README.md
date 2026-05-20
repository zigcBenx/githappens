# GitHappens ⚡

CLI tool for GitLab: create issues, merge requests, file reviews, and deployment tracking — without leaving your terminal.

## New Modular Structure

```
gitHappens/
├── main.py                  # Entry point and CLI argument parsing
├── gitlab_api.py            # GitLab API interactions and glab CLI wrappers
├── config.py                # Configuration management (lazy-loaded)
├── templates.py             # Template and reviewer selection UI
├── git_utils.py             # Git operations: commit history, AI summaries
├── interactive.py           # Interactive inquirer-based prompts
├── gitHappens.py            # Backwards-compatible entry point shim
├── configs/
│   ├── config.ini            # User configuration (copy from .example)
│   └── templates.json        # Issue templates and reviewer config
└── commands/                # Domain-grouped command modules
    ├── __init__.py           # Backwards-compatible re-exports
    ├── create_issue.py        # Issue creation logic
    ├── review.py             # Review workflow
    ├── deploy.py             # Deployment checks
    └── open_mr.py            # Merge request operations
```

## Requirements

- Python 3 with pip
- [glab CLI](https://gitlab.com/gitlab-org/cli) — install and authenticate with `glab auth login`
- `pip install inquirer requests`

## Setup

1. Clone the repository
2. Copy config examples:
   ```
   cp configs/config.ini.example configs/config.ini
   cp configs/templates.json.example configs/templates.json
   ```
3. Edit `configs/config.ini`:
   - Set `group_id` to your GitLab group ID (for fetching milestones/epics)
   - Set `GITLAB_TOKEN` (or leave empty if using `glab auth`)

## Running

```bash
# Create an issue (with interactive prompts)
python3 gitHappens.py "My new feature idea"

# Create issue + MR + branch in one shot
python3 gitHappens.py "Fix login bug" -m

# Just open an issue (no MR)
python3 gitHappens.py "My issue" --only_issue

# Open current MR in browser
python3 gitHappens.py open

# Review workflow (add reviewers + AI review)
python3 gitHappens.py review --select
python3 gitHappens.py review --auto_merge

# Commit summaries
python3 gitHappens.py summary        # last 2 weeks
python3 gitHappens.py summaryAI      # AI-powered summary

# Last production deployment info
python3 gitHappens.py "last deploy"

# Report an incident
python3 gitHappens.py report "API timeout" 30
```

## Configuration

### templates.json

```json
{
    "templates": [
      { "name": "Bug easy", "weight": 1, "labels": ["Bug"] },
      { "name": "Feature medium", "weight": 5, "labels": ["feature"], "onlyIssue": true }
    ],
    "reviewers": [123, 456],
    "productionMappings": {}
}
```