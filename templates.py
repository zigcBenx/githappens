"""Template and reviewer selection."""
import inquirer
from config import get_templates_data, get_custom_template, get_gitlab_token, get_api_url


def select_template():
    TEMPLATES, _, _ = get_templates_data()
    template_names = [t['name'] for t in TEMPLATES]
    template_names.append(get_custom_template())
    answer = inquirer.prompt([
        inquirer.List('template', message="Select template:", choices=template_names),
    ])
    return answer['template']


def getIssueSettings(template_name):
    TEMPLATES, _, _ = get_templates_data()
    if template_name == get_custom_template():
        return {}
    return next((t for t in TEMPLATES if t['name'] == template_name), None)


def select_epic(epics):
    epics = [t['title'] for t in epics]
    search_query = inquirer.prompt([
        inquirer.Text('search_query', message='Search epic:'),
    ])['search_query']
    filtered = [c for c in epics if search_query.lower() in c.lower()]
    answer = inquirer.prompt([
        inquirer.List('epics', message="Select epic:", choices=filtered),
    ])
    return answer['epics']


def getSelectedEpic(epic, epics):
    return next((t for t in epics if t['title'] == epic), None)


def selectLabels(search, multiple=False):
    from gitlab_api import getLabelsOfGroup
    labels = sorted([t['name'] for t in getLabelsOfGroup(search)])
    qt = inquirer.Checkbox if multiple else inquirer.List
    answer = inquirer.prompt([
        qt('labels', message="Select one or more department labels:", choices=labels),
    ])
    return answer['labels']


def chooseReviewersManually():
    _, REVIEWERS, _ = get_templates_data()
    reviewer_choices = []
    for reviewer_id in REVIEWERS:
        api_url = f"{get_api_url()}/users/{reviewer_id}"
        try:
            import requests as _req
            response = _req.get(api_url, headers={"Private-Token": get_gitlab_token()})
            if response.status_code == 200:
                user = response.json()
                display_name = f"{user.get('name')} ({user.get('username')})"
                reviewer_choices.append((display_name, str(reviewer_id)))
            else:
                reviewer_choices.append((str(reviewer_id), str(reviewer_id)))
        except Exception:
            reviewer_choices.append((str(reviewer_id), str(reviewer_id)))
    answers = inquirer.prompt([
        inquirer.Checkbox('selected_reviewers', message="Select reviewers",
                          choices=[(n, r) for n, r in reviewer_choices]),
    ])
    if answers and "selected_reviewers" in answers:
        return [int(r) for r in answers["selected_reviewers"]]
    return []