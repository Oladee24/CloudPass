from app import create_app, db
from app.services import seed_default_routes


app = create_app()

# Creates the database tables if they do not exist yet.
with app.app_context():
    db.create_all()
    seed_default_routes()


if __name__ == "__main__":
    app.run(debug=True)
