<div align="center">
  <h1>GitHappens⚡</h1>
  <h2>CLI that lets you open merge requests, file issues, and request reviews without leaving your terminal</h2>
  <img src="https://github.com/user-attachments/assets/f18c0f04-edef-467c-b833-019643642beb" alt="GitHappens demo" />
</div>

## Getting Started 🚀

GitHappens is a Python CLI for GitLab workflows. It can create GitLab issues,
branches, and merge requests from templates, request reviewers, track time,
run AI review, show recent commit summaries, and inspect the last production
deployment.

## Installation 🔨

### Prerequisites

- Install Python 3 with pip.
- Install [glab](https://gitlab.com/gitlab-org/cli).
- Authorize glab with `glab auth login`. A GitLab access token is required;
  SSH is recommended for repository access.
- Install Python dependencies:

```sh
pip install -r requirements.txt
```

### Setup

Clone this repository to a local path that you plan to keep. The shell alias
points to this checkout, so moving or deleting it will break the command.

Copy the example configuration files:

```sh
cp configs/templates.json.example configs/templates.json
cp configs/config.ini.example configs/config.ini
```

In `configs/config.ini`, set at least:

- `group_id`: GitLab group ID used for milestones, iterations, epics, and
  labels.
- `GITLAB_TOKEN`: GitLab token used for API requests.

Optional settings include:

- `developer_email`: filters `gh summary` output to commits by this email.
- `OPENAI_API_KEY`: enables AI summaries and AI code review.
- `incident_project_id`: target project for `gh report`.
- `squash_commits` and `delete_branch_after_merge`: merge request defaults.

Edit `configs/templates.json` to configure issue templates, reviewer IDs, and
production deployment mappings. The example file contains comments for
explanation, but JSON itself does not allow comments; remove comments before
using the file as `configs/templates.json`.

### Alias

Add an alias to your shell config:

```sh
alias gh='python3 /path/to/githappens/gitHappens.py'
```

Reload the matching shell config:

```sh
source ~/.zshrc
```

Use `source ~/.bashrc` instead if you added the alias to Bash.

## Usage ⚡

Run `gh` or `gh --help` to see available flags.

### Create An Issue And Merge Request

Pass the issue title as the command argument:

```sh
gh "Implement account export"
```

GitHappens asks for a template, then creates the issue, branch, and merge
request unless the selected template or CLI flags request issue-only mode.

### Project Selection

Project selection is resolved in this order:

1. `projectIds` from the selected template.
2. `--project_id=<id-or-url-encoded-path>`.
3. The GitLab project detected from the current directory's `origin` remote.
4. An interactive project ID prompt.

Example:

```sh
gh "Fix login redirect" --project_id=123456
```

### Multiple Projects

Use `projectIds` in a template when the same issue should be created across
multiple projects, such as backend and frontend repositories:

```json
{
  "name": "Feature issue for API and frontend",
  "labels": ["feature::Confirmed"],
  "projectIds": [123, 456]
}
```

### Templates

Issue templates live in `configs/templates.json`. Template names must be unique.

Common template keys:

- `name`: template display name.
- `weight`: GitLab issue weight.
- `labels`: labels to apply.
- `projectIds`: one or more GitLab project IDs.
- `onlyIssue`: create only the issue.
- `type`: GitLab issue type, such as `issue` or `incident`.

### Milestones, Iterations, And Epics

By default, GitHappens selects the current milestone, prompts for an iteration,
and prompts for an epic.

Use these flags to change that behavior:

- `-m` or `--milestone`: choose the milestone manually.
- `--no_milestone`: skip milestone selection.
- `--no_iteration`: skip iteration selection.
- `--no_epic`: skip epic selection.

### Issue-Only Mode

Use `--only_issue` when you do not want GitHappens to create a branch or merge
request:

```sh
gh "Write migration notes" --only_issue
```

You can also make this the default for a template:

```json
{
  "name": "Feature issue for later",
  "labels": ["feature::Confirmed"],
  "onlyIssue": true
}
```

### Open The Current Merge Request

Open the merge request for the current branch in your browser:

```sh
gh open
```

### Request Review

Set default reviewer IDs in `configs/templates.json`:

```json
{
  "templates": [],
  "reviewers": [234, 456, 678]
}
```

Request review for the merge request on the current branch:

```sh
gh review
```

Select reviewers manually:

```sh
gh review --select
```

Enable auto-merge when the pipeline succeeds:

```sh
gh review --auto_merge
gh review -am
```

When `OPENAI_API_KEY` is configured, `gh review` also runs AI code review for
the branch diff and posts feedback to the merge request.

### AI Code Review

Run AI code review locally without the rest of the review flow:

```sh
gh ai review
```

### Commit Summaries

Show recent commits from the last two weeks:

```sh
gh summary
```

Generate an AI summary of those commits:

```sh
gh summaryAI
```

### Incident Reports

Create and close an incident issue, then add spent time:

```sh
gh report "Short incident description" 30
```

Set `incident_project_id` in `configs/config.ini` before using this command.

### Last Production Deployment

Show the most recent successful production deployment for the current project:

```sh
gh last deploy
```

Configure project-specific deployment detection in `configs/templates.json`:

```json
{
  "templates": [],
  "reviewers": [],
  "productionMappings": {
    "your_project_id": {
      "stage": "production:deploy",
      "job": "deploy-to-production"
    },
    "another_project_id": {
      "stage": "deploy",
      "job": "production:deploy"
    }
  }
}
```

Only successful jobs are considered production deployments.

## Troubleshooting 🪲🔫

### 401 Unauthorized

If you get `glab: 401 Unauthorized (HTTP 401)`, run `glab auth login` again,
check `GITLAB_TOKEN` in `configs/config.ini`, and reopen your terminal.

### Missing Config Files

Make sure both local config files exist:

```sh
ls configs/config.ini configs/templates.json
```

If either file is missing, copy it from the matching `.example` file and fill in
the required values.

## Contributing 🫂🫶

Every contributor is welcome. GitLab's
[merge requests API documentation](https://docs.gitlab.com/ee/api/merge_requests.html)
is a useful reference.

## Donating 💜

Make sure to check this project on
[OpenPledge](https://app.openpledge.io/repositories/zigcBenx/gitHappens).
