import inquirer

def select_template(templates):
    template_names = [t['name'] for t in templates]
    template_names.append("Custom") # This should be CUSTOM_TEMPLATE value usually
    questions = [
        inquirer.List('template',
                      message="Select template:",
                      choices=template_names,
                      ),
    ]
    answer = inquirer.prompt(questions)
    return answer['template']

def select_milestone(milestones):
    milestone_names = [t['title'] for t in milestones]
    questions = [
        inquirer.List('milestones',
                      message="Select milestone:",
                      choices=milestone_names,
                      ),
    ]
    answer = inquirer.prompt(questions)
    return answer['milestones']

def select_iteration(iterations):
    iteration_names = [t['start_date'] + ' - ' + t['due_date'] for t in iterations]
    questions = [
        inquirer.List('iterations',
                      message="Select iteration:",
                      choices=iteration_names,
                      ),
    ]
    answer = inquirer.prompt(questions)
    return answer['iterations']

def select_epic(epics):
    epic_names = [t['title'] for t in epics]
    search_query = inquirer.prompt([
        inquirer.Text('search_query', message='Search epic:'),
    ])['search_query']
    filtered_epics = [c for c in epic_names if search_query.lower() in c.lower()]
    questions = [
        inquirer.List('epics',
                      message="Select epic:",
                      choices=filtered_epics,
                      ),
    ]
    answer = inquirer.prompt(questions)
    return answer['epics']

def prompt_estimated_time():
    return inquirer.prompt([
        inquirer.Text('estimated_time',
                      message='Estimated time to complete this issue (in minutes, optional)',
                      validate=lambda _, x: x == '' or x.isdigit())
    ])['estimated_time']

def select_labels(labels, multiple=False):
    question_type = inquirer.Checkbox if multiple else inquirer.List
    questions = [
        question_type(
            'labels',
            message="Select one or more department labels:",
            choices=labels,
        ),
    ]
    answer = inquirer.prompt(questions)
    return answer['labels']

def prompt_spent_time():
    return inquirer.prompt([
        inquirer.Text('spent_time',
                      message='How many minutes did you actually spend on this issue?',
                      validate=lambda _, x: x.isdigit())
    ])['spent_time']

def prompt_reviewers(reviewer_choices):
    questions = [
        inquirer.Checkbox(
            "selected_reviewers",
            message="Select reviewers",
            choices=[(name, str(rid)) for name, rid in reviewer_choices],
        )
    ]
    answers = inquirer.prompt(questions)
    if answers and "selected_reviewers" in answers:
        return [int(r) for r in answers["selected_reviewers"]]
    else:
        return []
