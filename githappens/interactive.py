def prompt_list(name, message, choices):
    import inquirer

    return inquirer.prompt(
        [inquirer.List(name, message=message, choices=choices)]
    )


def prompt_checkbox(name, message, choices):
    import inquirer

    return inquirer.prompt(
        [inquirer.Checkbox(name, message=message, choices=choices)]
    )


def prompt_text(name, message, validate=None):
    import inquirer

    kwargs = {"message": message}
    if validate is not None:
        kwargs["validate"] = validate
    return inquirer.prompt([inquirer.Text(name, **kwargs)])
