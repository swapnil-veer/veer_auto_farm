from flask import Blueprint, render_template, current_app

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def home():

    # state = current_app.ctx.system_state
    state = current_app.extensions["ctx"].system_state


    return render_template(
        "home/index.html",
        state=state
    )