from flask import (
    Blueprint,
    render_template,
    redirect,
    current_app,
)

dev_bp = Blueprint("dev", __name__)


@dev_bp.route("/dev/simulator")
def simulator():

    ctx = current_app.extensions["ctx"]
    state = current_app.extensions["ctx"].system_state.snapshot()
    motor_running = state["pump_running"]

    lcd_lines = ctx.lcd_driver.get_lines()

    return render_template(
        "dev/simulator.html",
        motor_running=motor_running,
        lcd_lines=lcd_lines,
    )


@dev_bp.route("/dev/current/<mode>", methods=["POST"])
def set_current_mode(mode):

    ctx = current_app.extensions["ctx"]

    ctx.current_sensor.set_mode(mode)

    return redirect("/dev/simulator")


@dev_bp.route("/dev/power/on", methods=["POST"])
def power_on():

    ctx = current_app.extensions["ctx"]

    if hasattr(ctx.phase_gpio, "set_power"):
        ctx.phase_gpio.set_power(True)

    return redirect("/dev/simulator")


@dev_bp.route("/dev/power/off", methods=["POST"])
def power_off():

    ctx = current_app.extensions["ctx"]

    if hasattr(ctx.phase_gpio, "set_power"):
        ctx.phase_gpio.set_power(False)

    return redirect("/dev/simulator")