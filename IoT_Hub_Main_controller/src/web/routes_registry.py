from web.routes.home_routes import home_bp
from web.routes.dev_routes import dev_bp
from web.routes.sms_routes import sms_bp

def register_routes(app):

    app.register_blueprint(home_bp)
    app.register_blueprint(dev_bp)
    app.register_blueprint(sms_bp)