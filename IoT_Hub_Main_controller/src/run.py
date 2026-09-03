from app import create_app, db

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

# from database.models import User
# user = User (phone = "+917038835527", name = "Swapnil", email = "veerswapnil00@gmail.com", is_owner = True, is_superuser = True)
# with app.app_context():
#     db.session.add(user)
#     db.session.commit()

if __name__ == "__main__":

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000,
    )