<div align="center">
  <h1>GitHappens⚡</h1>
  <h2>CLI that lets you open merge requests, file issues, and request reviews without leaving your terminal</h2>
  <img src="https://github.com/user-attachments/assets/f18c0f04-edef-467c-b833-019643642beb" alt="GitHappens demo" />
</div>

## Installation 🔨

### Prerequisites

- Install Python 3 and make sure pip is included.
- Install [glab](https://gitlab.com/gitlab-org/cli).
- Authorize glab with `glab auth login`. You will need a GitLab access token; SSH is recommended.
- Install the Python dependencies:

```sh
pip install -r requirements.txt
```

### Setup

- Clone the repository to your local machine in a location you will keep.

#### Setup configs

- In the `configs` folder, copy the example files:

```sh
cp configs/templates.json.example configs/templates.json
cp configs/config.ini.example configs/config.ini
```

- In `config.ini`, set your GitLab group ID as `group_id`. This is used for fetching milestones, iterations, labels, and epics.
- In `config.ini`, set `GITLAB_TOKEN` to a GitLab token with access to the projects you want to manage.
- You can adjust templates now or later. If you edit `templates.json`, remove comments before running the command because JSON does not support comments.

#### Alias

To run the GitHappens script anywhere in the filesystem, create an alias.
Add the following line to your `.bashrc` or `.zshrc` file:

```sh
alias gh='python3 ~/<path-to-githappens-project>/gitHappens.py'
```

Run `source ~/.zshrc` or restart your terminal.

## Usage ⚡

### Project selection

- Project selection is automatic if you run the script from inside a GitLab project checkout.
- You can specify a project ID or URL-encoded path with `--project_id=123456`.
- If neither of the above applies, the program prompts you for `project_id`.

#### Issue creation for multiple projects at once

This feature is useful when you have to create the same issue on both backend and frontend projects.

- You can specify a list of IDs in `templates.json`.

```json
...
{
  "name": "Feature issue for API and frontend",
  ...
  "projectIds": [123, 456]
}
...
```

### Milestone selection

Milestone is set to current by default. If you want to pick it manually, pass the `-m` or `--milestone` flag.

### Issue templates

Issue templates are located in `configs/templates.json`.

**Make sure template names are unique.**

### Excluding features

If you do not want to include some settings, use the following flags:

- `--no_epic` - no epic will be selected or prompted
- `--no_milestone` - no milestone will be selected or prompted
- `--no_iteration` - no iteration will be selected or prompted

### Only issue

If you are in a hurry and want to create an issue for later without a merge request and branch, use this flag.

- `--only_issue` - no merge request nor branch will be created.
  You can achieve the same functionality by adding the `onlyIssue` key to `templates.json`.

```json
...
{
  "name": "Feature issue for later",
  ...
  "onlyIssue": true
}
...
```

### Open merge request in browser

You can open the merge request for the currently checked-out branch in your browser:

```sh
gh open
```

### Git review

You can set default reviewers in `templates.json`.

```json
...
{
  "templates": [
    ...
  ],
  ...
  "reviewers": [234, 456, 678]
}
...
```

To submit a merge request into review, run:

```sh
gh review
```

To also enable **auto-merge when the pipeline succeeds**, add the `--auto_merge` or `-am` flag:

```sh
gh review --auto_merge

gh review -am
```

### Manually selecting reviewers

To manually select reviewers for your merge request, use the `--select` flag with the review command:

```sh
gh review --select
```

You will be prompted with an interactive list of reviewers to choose from.

### Commit summary

You can print commits from the last two weeks:

```sh
gh summary
```

If `OPENAI_API_KEY` is configured in `config.ini` and the `openai` Python package is installed, you can generate an AI summary:

```sh
gh summaryAI
```

### Last production deployment

You can check when the last successful production deployment occurred:

```sh
gh last deploy
```

This command shows information about the most recent successful production deployment including timing, pipeline details, and how long ago it happened.

#### Configuration

To configure production deployment detection, add project-specific mappings to your `templates.json`:

```json
{
  "templates": [...],
  "reviewers": [...],
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

**Note:** The command only considers deployments with "success" status to ensure accurate last deployment information.

### Incident report

You can create and immediately close an incident issue with time tracking:

```sh
gh report "Incident title" 30
```

Configure `incident_project_id` in `config.ini` before using this command.

### AI code review

You can run an AI code review for the current repository:

```sh
gh ai review
```

### Flag help

If you run just `gh` (or whatever alias you set) or `gh --help`, you will see all available flags and a short explanation.

## Troubleshooting 🪲🔫

### Receiving 401 Unauthorized error

If you get `glab: 401 Unauthorized (HTTP 401)` when using GitHappens, repeat `glab auth login` and then reopen your terminal.

## Contributing 🫂🫶

Every contributor is welcome.
I suggest checking GitLab's official API documentation: https://docs.gitlab.com/ee/api/merge_requests.html

## Donating 💜

Make sure to check this project on [OpenPledge](https://app.openpledge.io/repositories/zigcBenx/gitHappens).
