from app import create_app

from web.routes_registry import register_routes

from infrastructure.bootstrap import (
    bootstrap_database,
)

from main import (
    start_application,
)


app = create_app()

register_routes(app)

bootstrap_database(app)

ctx = start_application(app)


if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000,
    )