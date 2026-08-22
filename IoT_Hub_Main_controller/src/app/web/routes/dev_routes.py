from flask import Blueprint, render_template, current_app

current_app.extensions["ctx"].LCDDriver

from composition import provider

lcd = provider.get_lcd
current_sensor = provider.get_current_sensor
pump_gpio = provider.get_pump_gpio
phase_gpio = provider.get_phase_gpio
sim_modem = provider.get_sim


from flask import (
    Blueprint,
    render_template,
    redirect
)

dev_bp = Blueprint("dev", __name__)


@dev_bp.route("/dev/motor")
def motor():

    return render_template(
        "dev/motor.html",
        motor_running=pump_gpio.is_on()
    )


@dev_bp.route("/dev/lcd")
def lcd():

    lines = lcd.get_lines()

    return render_template(
        "dev/lcd.html",
        line1=lines[1],
        line2=lines[2],
        line3=lines[3],
        line4=lines[4]
    )


@dev_bp.route("/dev/current")
def current():

    return render_template(
        "dev/current.html"
    )


@dev_bp.route(
    "/dev/current/normal",
    methods=["POST"]
)
def normal():

    current_sensor.set_mode(
        current_sensor.NORMAL
    )

    return redirect("/dev/current")


@dev_bp.route(
    "/dev/current/dry-run",
    methods=["POST"]
)
def dry_run():

    current_sensor.set_mode(
        current_sensor.DRY_RUN
    )

    return redirect("/dev/current")


@dev_bp.route(
    "/dev/current/motor-stopped",
    methods=["POST"]
)
def stopped():

    current_sensor.set_mode(
        current_sensor.MOTOR_STOPPED
    )

    return redirect("/dev/current")


@dev_bp.route(
    "/dev/current/stop-failure",
    methods=["POST"]
)
def stop_failure():

    current_sensor.set_mode(
        current_sensor.STOP_FAILURE
    )

    return redirect("/dev/current")