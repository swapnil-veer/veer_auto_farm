from flask import (
    Blueprint,
    render_template,
    redirect,
    request,
    current_app,
)

dev_bp = Blueprint("dev", __name__)


@dev_bp.route("/dev/simulator")
def simulator():

    ctx = current_app.extensions["ctx"]

    lcd_lines = ctx.lcd_driver.get_lines()

    motor_running = ctx.pump_service.is_running()

    current_mode = ctx.current_sensor.get_mode()

    power_available = ctx.phase_monitor.is_power_available()

    return render_template(
        "dev/simulator.html",
        motor_running=motor_running,
        lcd_lines=lcd_lines,
        current_mode=current_mode,
        power_available=power_available,
    )


@dev_bp.route("/dev/current-mode", methods=["POST"])
def current_mode():

    ctx = current_app.extensions["ctx"]

    mode = request.form.get("mode")

    ctx.current_sensor.set_mode(mode)

    return redirect("/dev/simulator")


@dev_bp.route("/dev/power-mode", methods=["POST"])
def power_mode():

    ctx = current_app.extensions["ctx"]

    power = request.form.get("power")

    if power == "on":
        ctx.phase_gpio.set_power(True)
    else:
        ctx.phase_gpio.set_power(False)

    return redirect("/dev/simulator")