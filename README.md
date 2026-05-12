<div align="center">
  <h1>GitHappens⚡</h1>
  <h2>CLI that lets you open merge requests, file issues, and request reviews without leaving your terminal</h2>
  <img src="https://github.com/user-attachments/assets/f18c0f04-edef-467c-b833-019643642beb" alt="GitHappens demo" />
</div>

## Getting started 🚀

GitHappens is a Python CLI for GitLab workflows. It can create issues,
branches, and merge requests from templates, open the merge request for the
current branch, request reviewers, track time, run AI review, and show recent
deployment or commit activity.

## Installation 🔨

### Prerequisites

- Install Python 3 with pip.
- Install [glab](https://gitlab.com/gitlab-org/cli).
- Authorize glab with `glab auth login`. You need a GitLab access token; SSH is
  recommended.
- Install Python dependencies:

```sh
pip install -r requirements.txt
```

### Setup

Clone this repository to a local path that you will keep available, because the
CLI alias points to this checkout.

#### Configure GitHappens

Copy the example configuration files:

```sh
cp configs/templates.json.example configs/templates.json
cp configs/config.ini.example configs/config.ini
```

In `configs/config.ini`, set at least:

- `group_id`: your GitLab group ID. This is used to fetch milestones,
  iterations, epics, and labels.
- `GITLAB_TOKEN`: a GitLab token with access to the target projects.

Optional settings include:

- `developer_email`: filters `gh summary` output to commits by this email.
- `OPENAI_API_KEY`: enables AI summaries and AI code review.
- `incident_project_id`: target project for `gh report`.

Update `configs/templates.json` for your issue templates, reviewers, and
production deployment mappings. The example file contains comments for
explanation, but JSON does not allow comments; remove them before running the
CLI.

#### Alias

To run GitHappens anywhere, add an alias to your `.bashrc` or `.zshrc`:

```sh
alias gh='python3 ~/<path-to-githappens-project>/gitHappens.py'
```

Reload your shell:

```sh
source ~/.zshrc
```

Use the matching file for your shell, for example `source ~/.bashrc` if you
added the alias there.

## Usage ⚡

Run `gh` or `gh --help` to see all available flags.

### Create an issue and merge request

Pass the issue title as the command argument:

```sh
gh "Implement account export"
```

GitHappens prompts you to choose a template, then creates the GitLab issue,
branch, and merge request unless the selected template or CLI flags say to
create only an issue.

### Project selection

Project selection is resolved in this order:

1. `projectIds` from the selected template.
2. `--project_id=<id-or-url-encoded-path>`.
3. The GitLab project detected from the current directory's `origin` remote.
4. An interactive prompt for the project ID.

Example:

```sh
gh "Fix login redirect" --project_id=123456
```

#### Create issues for multiple projects

Add `projectIds` to a template when the same issue should be created for
multiple projects, such as backend and frontend repositories:

```json
{
  "name": "Feature issue for API and frontend",
  "labels": ["feature::Confirmed"],
  "projectIds": [123, 456]
}
```

### Milestones, iterations, and epics

By default, GitHappens selects the current milestone, prompts for an iteration,
and prompts for an epic.

Use these flags to change that behavior:

- `-m` or `--milestone`: choose the milestone manually.
- `--no_milestone`: skip milestone selection.
- `--no_iteration`: skip iteration selection.
- `--no_epic`: skip epic selection.

### Issue templates

Issue templates live in `configs/templates.json`.

Template names must be unique. Supported keys include:

- `name`: template display name.
- `weight`: GitLab issue weight.
- `labels`: labels to apply.
- `projectIds`: one or more GitLab project IDs.
- `onlyIssue`: create only the issue, without a branch or merge request.
- `type`: GitLab issue type, such as `issue` or `incident`.

### Create only an issue

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

### Open the current merge request

Open the merge request for the current branch in your browser:

```sh
gh open
```

### Request review

Set default reviewers in `configs/templates.json`:

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

To select reviewers manually, add `--select`:

```sh
gh review --select
```

To enable auto-merge when the pipeline succeeds, add `--auto_merge` or `-am`:

```sh
gh review --auto_merge
gh review -am
```

When `OPENAI_API_KEY` is configured, `gh review` also runs AI code review for
the branch diff and posts feedback to the merge request.

### AI code review

Run AI code review locally without posting to GitLab:

```sh
gh ai review
```

This compares the current branch with the default branch and prints findings in
the terminal.

### Commit summaries

Show recent commits from the last two weeks:

```sh
gh summary
```

Generate an AI summary of those commits:

```sh
gh summaryAI
```

### Incident report

Create and close an incident issue, then add spent time:

```sh
gh report "Short incident description" 30
```

Set `incident_project_id` in `configs/config.ini` before using this command.

### Last production deployment

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

Only deployments with a `success` status are considered.

## Troubleshooting 🪲🔫

### Receiving 401 Unauthorized errors

If you get `glab: 401 Unauthorized (HTTP 401)`, run `glab auth login` again,
check `GITLAB_TOKEN` in `configs/config.ini`, and reopen your terminal.

### Missing or invalid config files

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
