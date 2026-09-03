from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    current_app,
)
from urllib.parse import quote, unquote_plus
from database.models.sms_log import SmsDirection
from database.models.user import User

sms_bp = Blueprint("sms", __name__)

def normalize_phone(phone):
    if not phone:
        return None

    phone = phone.strip()

    if phone.startswith("+"):
        return phone

    if phone.startswith("91") and len(phone) == 12:
        return f"+{phone}"

    if len(phone) == 10:
        return f"+91{phone}"

    return phone

@sms_bp.route("/dev/msg_interface")
def msg_interface():

    ctx = current_app.extensions["ctx"]

    selected_phone = request.args.get("phone")
    if selected_phone:
        selected_phone = normalize_phone(request.form.get("phone"))

    users = (
        User.query
        .filter_by(is_active=True)
        .order_by(User.name)
        .all()
    )

    if not selected_phone and users:
        selected_phone = users[0].phone

    incoming = []
    outgoing = []

    if selected_phone:

        incoming = ctx.sms_repo.get_sms_logs(
            phone=selected_phone,
            direction=SmsDirection.INCOMING
        )

        outgoing = ctx.sms_repo.get_sms_logs(
            phone=selected_phone,
            direction=SmsDirection.OUTGOING
        )

        incoming = sorted(
            incoming,
            key=lambda x: x["created_at"],
            reverse=True
        )[:5]

        outgoing = sorted(
            outgoing,
            key=lambda x: x["created_at"],
            reverse=True
        )[:5]

    return render_template(
        "dev/msg_interface.html",
        users=users,
        selected_phone=selected_phone,
        incoming=incoming,
        outgoing=outgoing,
    )


@sms_bp.route(
    "/dev/msg_interface/send",
    methods=["POST"]
)
def send_sms():

    ctx = current_app.extensions["ctx"]

    phone = normalize_phone(request.form.get("phone"))
    message = request.form.get("message")
    if phone and message:

        ctx.sim_modem.inject_sms(
            phone=phone,
            message=message
        )

    return redirect(f"/dev/msg_interface?phone={quote(phone, safe='')}")