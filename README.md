<div align="center">
  <h1>GitHappens⚡</h1>
  <h2>CLI that lets you open merge requests, file issues, and request reviews without leaving your terminal</h2>
  <img src="https://github.com/user-attachments/assets/f18c0f04-edef-467c-b833-019643642beb" alt="GitHappens demo" />
</div>

## Getting started 🚀

## Installation 🔨

### Prerequisites

- Install Python 3 with pip.
- Install [glab](https://gitlab.com/gitlab-org/cli).
- Authorize glab with `glab auth login`. You will need a GitLab access token, and SSH is recommended for repository access.
- Install Python dependencies:

```sh
pip install -r requirements.txt
```

### Setup

- Clone this repository to a local path that you plan to keep. The shell alias points to this checkout, so moving or deleting it later will break the command.

#### Setup configs

- In the `configs` folder, copy the example files:

```sh
cp configs/templates.json.example configs/templates.json
cp configs/config.ini.example configs/config.ini
```

- In `configs/config.ini`, paste your GitLab group ID into `group_id`. This is used for fetching milestones and epics.
- You can adjust templates now, or later. Remove comments from `configs/templates.json` before running the command because JSON does not support comments.

#### Alias

To run gitHappens script anywhere in the filesystem, create an alias.
Add the following line to your `.bashrc` or `.zshrc` file:

```sh
alias gh='python3 /path/to/githappens/gitHappens.py'
```

Run `source ~/.zshrc` or restart terminal.

## Usage ⚡

### Project selection

- Project selection is made automatically if you run the script from the same path as your project.
- You can specify a project ID or URL-encoded path as a script argument, for example: `--project_id=123456`.
- If neither of the steps above apply, the program prompts you for a `project_id`.

#### Issue creation for multiple projects at once

This feature is useful if you have to create issue on both backend and frontend project for same thing.

- You can specify list of ids in `templates.json` file.

```json
{
  "name": "Feature issue for API and frontend",
  "labels": ["feature::Confirmed"],
  "projectIds": [123, 456]
}
```

### Milestone selection

Milestone is set to current by default. If you want to pick it manually, pass `-m` or `--milestone` flag to the script.

### Issue templates

Issue templates are located in `configs/templates.json`.

Make sure that template names are unique.

### Excluding features

If you don't want to include some settings you use following flags:

- `--no_epic` - no epic will be selected or prompted
- `--no_milestone` - no milestone will be selected or prompted

### Only issue

If you are in a hurry and want to create issue for later without merge request and branch this flag is for you.

- `--only_issue` - no merge request or branch will be created.
  You can achieve the same behavior by adding an `onlyIssue` key to `templates.json`.

```json
{
  "name": "Feature issue for later",
  "labels": ["feature::Confirmed"],
  "onlyIssue": true
}
```

### Open merge request in browser

You can open merge request for current checked out branch in browser with command:

```sh
gh open
```

### Git review

You can set default reviewers in templates.json file.

```json
{
  "templates": [],
  "reviewers": [234, 456, 678]
}
```

To submit merge request into review run command:

```sh
gh review
```

To also enable **auto-merge when the pipeline succeeds**, add `--auto_merge` or `-am` flag:

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

### Flag help

If you run just `gh` (or whatever alias you set) or `gh --help` you will see all available flags and a short explanation.

## Troubleshooting 🪲🔫

### Receiving 401 Unauthorized error

If you get `glab: 401 Unauthorized (HTTP 401)` when using GitHappens, you must repeat `glab auth login`
and then reopen your terminal.

## Contributing 🫂🫶

Every contributor is welcome.
I suggest checking [GitLab's official API documentation](https://docs.gitlab.com/ee/api/merge_requests.html).

## Donating 💜

Make sure to check this project on [OpenPledge](https://app.openpledge.io/repositories/zigcBenx/gitHappens).
