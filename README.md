<div align="center">
  <h1>GitHappens⚡</h1>

  Githappens is a powerful and versatile open-source command-line interface (CLI) tool designed to streamline your GitLab workflow. <br>
  Whether you're managing one project or several, this tool offers a range of features to make issue and merge request management a breeze.
  <div align="right">- ChatGPT</div>
</div>

## Getting started 🚀

## Installation 🔨

### Preresequisits

- install python3 (make sure to include pip in install)
- Install [glab](https://gitlab.com/gitlab-org/cli)
- Authorize via glab `glab auth login` (you will need Gitlab access token)
- `pip install inquirer`
- `pip install requests`

### Setup

- Clone repository to your local machine to whatever destination you want (just don't delete it later)

#### Setup configs
- In configs folder copy example files like so:
`cp configs/templates.json.example configs/templates.json`
`cp configs/config.ini.example configs/config.ini`
- In `configs.ini` you have to paste id of your group in Gitlab to `group_id` (This is for fetching milestones and epics)
- You can adjust templates now, or play with them later (however, you have to remove comments from json before running the command).
#### Alias 

To run gitHappens script anywhere in filesystem, make sure to create an alias.
Add following line to your `.bashrc` or `.zshrc` file
```alias gh='python3 ~/<path-to-githappens-project>/gitHappens.py'```

Run `source ~/.zshrc` or restart terminal.

## Usage ⚡

### Project selection

- Project selection is made automatically if you run script in same path as your project is located.
- You can specify project id or URL-encoded path as script argument e.g.: `--project_id=123456`
- If no of steps above happen, program will prompt you with question about project_id

#### Issue creation for multiple projects at once
This feature is useful if you have to create issue on both backend and frontend project for same thing.
- You can specify list of ids in `templates.json` file.
```
...
{
  "name": "Feature issue for API and frontend",
  ...
  "projectIds": [123, 456]
}
...
```

### Milestone selection

Milestone is set to current by default. If you want to pick it manually, pass `-m` or `--milestone` flag to the script.

### Issue templates
Issue templates are located in `configs/templates.json`.

**Make sure that names of templates are unique**


### Excluding features
If you don't want to include some settings you use following flags:
- `--no_epic` - no epic will be selected or prompted
- `--no_milestone` - no milestone will be selected or prompted


### Only issue
If you are in a hurry and want to create issue for later without merge request and branch this flag is for you.
- `--only_issue` - no merge request nor branch will be created.
You can achive same functionality with adding onlyIssue key to `templates.json` file (see example).
```
...
{
  "name": "Feature issue for later",
  ...
  "onlyIssue": true
}
...
```


### Open merge request in browser
You can open merge request for current checked out branch in browser with command:
```
gh open
```

### Git review
You can set default reviewers in templates.json (see example).
To submit merge request into review run command:
```
gh review
```


### Flag help
If you run just `gh` (or whatever alias you set) or `gh --help` you will see all available flags and short explanation.


## Contributing 🫂
Every contributor is welcome.
I suggest checking Gitlab's official API documentation: https://docs.gitlab.com/ee/api/merge_requests.html
