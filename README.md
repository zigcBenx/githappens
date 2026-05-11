<div align="center">
  <h1>GitHappens⚡</h1>
  <h2>CLI that lets you open merge requests, file issues, and request reviews without leaving your terminal</h2>
  <img src="https://github.com/user-attachments/assets/f18c0f04-edef-467c-b833-019643642beb" alt="GitHappens demo" />
</div>

## Getting started 🚀

GitHappens wraps the GitLab API so you can create issues, branches, merge
requests, reviewer assignments, and deployment checks from your terminal.

## Installation 🔨

### Prerequisites

- Install Python 3 and make sure `pip` is available.
- Install the [GitLab CLI (`glab`)](https://gitlab.com/gitlab-org/cli).
- Authenticate `glab` with `glab auth login`. You will need a GitLab access
  token. SSH is recommended for repository access.

### Setup

1. Clone the repository somewhere permanent on your machine.

   ```sh
   git clone https://github.com/zigcBenx/githappens.git
   cd githappens
   ```

2. Install the Python dependencies.

   ```sh
   python3 -m pip install -r requirements.txt
   ```

3. Copy the example configuration files.

   ```sh
   cp configs/templates.json.example configs/templates.json
   cp configs/config.ini.example configs/config.ini
   ```

4. Open `configs/config.ini` and set the required values.

   ```ini
   base_url=https://gitlab.com
   group_id=<your_gitlab_group_id>
   GITLAB_TOKEN=<your_gitlab_token>
   ```

   The same file also contains feature-specific settings such as
   `OPENAI_API_KEY`, `incident_project_id`, and production deployment defaults.

5. Adjust `configs/templates.json` for your issue templates, reviewers, and
   production deployment mappings.

   The example `templates.json` file contains comments at the top. Remove the
   comments before using it as strict JSON.

### Alias

To run GitHappens from any directory, add an alias to your `.bashrc` or
`.zshrc` file:

```sh
alias ghappens='python3 /path/to/githappens/gitHappens.py'
```

Reload your shell configuration:

```sh
source ~/.zshrc
```

You can choose any alias name. `ghappens` avoids conflicting with the GitHub
CLI command `gh`.

## Usage ⚡

### Project selection

Project selection is automatic when you run GitHappens from inside a GitLab
project checkout.

You can also pass a project ID or URL-encoded path:

```sh
ghappens --project_id=123456 "Issue title"
```

If the project cannot be detected and no project ID is provided, GitHappens
prompts you for one.

### Create an issue and merge request

Run GitHappens with an issue title:

```sh
ghappens "Add user profile settings"
```

By default, GitHappens creates an issue, branch, and merge request based on the
selected template.

### Create an issue only

Use `--only_issue` when you want to create an issue without creating a merge
request or branch:

```sh
ghappens --only_issue "Write follow-up documentation"
```

You can set the same behavior in a template:

```json
{
  "name": "Feature issue for later",
  "onlyIssue": true
}
```

### Create the same issue in multiple projects

This is useful when related backend and frontend projects need matching issues.
Add a `projectIds` list to a template in `configs/templates.json`:

```json
{
  "name": "Feature issue for API and frontend",
  "projectIds": [123, 456]
}
```

### Milestones, epics, and iterations

GitHappens can select GitLab metadata while creating issues.

By default, it uses the current active milestone and prompts you to select an
epic and iteration.

| Flag | Behavior |
| --- | --- |
| `-m`, `--milestone` | Choose a milestone manually instead of using the current milestone. |
| `--no_milestone` | Do not select or prompt for a milestone. |
| `--no_epic` | Do not select or prompt for an epic. |
| `--no_iteration` | Do not select or prompt for an iteration. |

### Issue templates

Issue templates are located in `configs/templates.json`.

Template names must be unique.

## Merge request workflow

### Open a merge request in the browser

Open the merge request for the currently checked-out branch:

```sh
ghappens open
```

### Submit a merge request for review

Set default reviewers in `configs/templates.json`:

```json
{
  "templates": [],
  "reviewers": [234, 456, 678]
}
```

Submit the current merge request for review:

```sh
ghappens review
```

The `review` command prompts for time spent on the linked issue before adding
reviewers.

Enable auto-merge when the pipeline succeeds:

```sh
ghappens review --auto_merge
ghappens review -am
```

Choose reviewers interactively:

```sh
ghappens review --select
```

GitHappens prompts you with a list of reviewers.

### AI review

GitHappens can run an AI review for the active merge request when
`OPENAI_API_KEY` is set in `configs/config.ini`:

```ini
OPENAI_API_KEY=<your_openai_api_key>
```

Run the review directly:

```sh
ghappens ai review
```

The `ghappens review` command also attempts to run the AI review after adding
reviewers. If the key or merge request context is missing, the AI review is
skipped.

## Reporting and summaries

### Create an incident report

Create a short incident report in the configured `incident_project_id` project:

```ini
incident_project_id=<your_incident_project_id>
```

```sh
ghappens report "Implemented the initial endpoint" 45
```

The final argument is the number of minutes spent. GitHappens creates the
incident issue, prompts for a department label, adds the spent time, and closes
the report.

### Summaries

Generate a recent commit summary:

```sh
ghappens summary
```

Generate an AI-assisted summary when `OPENAI_API_KEY` is configured:

```sh
ghappens summaryAI
```

## Last production deployment

Check when the last successful production deployment occurred:

```sh
ghappens last deploy
```

The command shows the most recent successful production deployment, including
pipeline status, job details, and how long ago it happened.

To configure production deployment detection, add project-specific mappings to
`configs/templates.json`. GitHappens checks the mapping for the current project:

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

## Help

After setup, run GitHappens without arguments, or with `--help`, to see
available flags:

```sh
ghappens --help
```

## Troubleshooting 🪲🔫

### Receiving a 401 Unauthorized error

If you get `glab: 401 Unauthorized (HTTP 401)`, repeat the `glab auth login`
flow and reopen your terminal.

If the error persists, generate a new GitLab access token and update
`GITLAB_TOKEN` in `configs/config.ini`.

### Configuration file not found

Make sure both files exist before running GitHappens:

```sh
ls configs/config.ini configs/templates.json
```

If either file is missing, copy the examples again:

```sh
cp configs/config.ini.example configs/config.ini
cp configs/templates.json.example configs/templates.json
```

## Contributing 🫂🫶

Every contributor is welcome.

For GitLab API details, check the
[official GitLab merge requests API documentation](https://docs.gitlab.com/ee/api/merge_requests.html).

## Donating 💜

Make sure to check this project on
[OpenPledge](https://app.openpledge.io/repositories/zigcBenx/githappens).
