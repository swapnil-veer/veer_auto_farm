from composition import compose_application


def start_application(app):

    ctx = compose_application(app)

    app.extensions["ctx"] = ctx

    return ctx