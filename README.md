<div align="center">
  <h1>GitHappens⚡</h1>
  <h2>CLI that lets you open merge requests, file issues, and request reviews without leaving your terminal</h2>
  <img src="https://github.com/user-attachments/assets/f18c0f04-edef-467c-b833-019643642beb" alt="GitHappens demo" />
</div>

## Getting started 🚀

### Prerequisites

- Install Python 3 and make sure `pip` is available.
- Install [glab](https://gitlab.com/gitlab-org/cli).
- Authorize `glab` with `glab auth login`. You will need a GitLab access
  token; SSH is recommended for repository access.

### Installation 🔨

1. Clone this repository somewhere permanent on your machine.

   ```sh
   git clone https://github.com/zigcBenx/gitHappens.git
   cd gitHappens
   ```

2. Install Python dependencies.

   ```sh
   pip install -r requirements.txt
   ```

3. Copy the example configuration files.

   ```sh
   cp configs/templates.json.example configs/templates.json
   cp configs/config.ini.example configs/config.ini
   ```

4. Open `configs/config.ini` and set the required values:

   - `group_id`: your GitLab group ID, used for fetching milestones and epics.
   - `GITLAB_TOKEN`: your GitLab access token.
   - `base_url`: your GitLab instance URL. The default is `https://gitlab.com`.

5. Adjust `configs/templates.json` for your issue templates, reviewers, and
   production deployment mappings.

   > [!NOTE]
   > The example `templates.json` file contains comments at the top. Remove
   > comments before using it as strict JSON.

### Alias

To run GitHappens from any directory, add an alias to your `.bashrc` or
`.zshrc` file:

```sh
alias ghappens='python3 /path/to/gitHappens/gitHappens.py'
```

Then reload your shell configuration:

```sh
source ~/.zshrc
```

You can choose any alias name. Avoid `gh` if you already use the GitHub CLI.

## Usage ⚡

### Project selection

Project selection is automatic when you run GitHappens from inside a GitLab
project checkout.

You can also pass a project ID or URL-encoded path:

```sh
ghappens --project_id=123456
```

If the project cannot be detected and no project ID is provided, GitHappens
prompts you for one.

### Issue creation for multiple projects at once

This is useful when you need to create the same issue in related backend and
frontend projects.

Add a `projectIds` list to a template in `configs/templates.json`:

```json
{
  "name": "Feature issue for API and frontend",
  "projectIds": [123, 456]
}
```

### Milestone selection

GitHappens uses the current milestone by default. To choose a milestone
manually, pass the `-m` or `--milestone` flag.

### Issue templates

Issue templates are located in `configs/templates.json`.

Template names must be unique.

### Excluding features

Use these flags when you want to skip optional issue metadata:

- `--no_epic`: do not select or prompt for an epic.
- `--no_milestone`: do not select or prompt for a milestone.

### Only issue

Use `--only_issue` when you want to create an issue without creating a merge
request or branch:

```sh
ghappens --only_issue
```

You can set the same behavior in a template:

```json
{
  "name": "Feature issue for later",
  "onlyIssue": true
}
```

### Open a merge request in the browser

Open the merge request for the currently checked-out branch:

```sh
ghappens open
```

### Git review

Set default reviewers in `configs/templates.json`:

```json
{
  "templates": [],
  "reviewers": [234, 456, 678]
}
```

Submit a merge request for review:

```sh
ghappens review
```

Enable auto-merge when the pipeline succeeds:

```sh
ghappens review --auto_merge
ghappens review -am
```

### Manually selecting reviewers

To choose reviewers interactively, use the `--select` flag:

```sh
ghappens review --select
```

GitHappens will prompt you with an interactive list of reviewers.

### Last production deployment

Check when the last successful production deployment occurred:

```sh
ghappens last deploy
```

The command shows the most recent successful production deployment, including timing, pipeline details, and how long ago it happened.

To configure production deployment detection, add project-specific mappings to
`configs/templates.json`:

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

### Flag help

Run GitHappens without arguments, or with `--help`, to see all available flags
and short explanations:

```sh
ghappens --help
```

## Troubleshooting 🪲🔫

### Receiving 401 Unauthorized

If you get `glab: 401 Unauthorized (HTTP 401)`, repeat the `glab auth login`
flow and reopen your terminal.

If the error persists, generate a new GitLab access token and update
`GITLAB_TOKEN` in `configs/config.ini`.

## Contributing 🫂🫶

Every contributor is welcome.

For GitLab API details, check the
[official GitLab merge requests API documentation](https://docs.gitlab.com/ee/api/merge_requests.html).

## Donating 💜

Make sure to check this project on [OpenPledge](https://app.openpledge.io/repositories/zigcBenx/gitHappens).
