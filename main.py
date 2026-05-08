from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from src.database import db
from src.bcrypt import bcrypt
import src.models
from src.routes.user_routes import user_app
from src.routes.book_routes import book_app
from src.routes.shelf_routes import shelf_app
from src.routes.goal_routes import goal_app


def create_app(config=None):
    app = Flask(__name__)
    app.config.from_object("src.config.Config")
    if config:
        app.config.update(config)

    db.init_app(app)
    bcrypt.init_app(app)
    jwt = JWTManager()
    jwt.init_app(app)
    CORS(app)

    app.register_blueprint(book_app)
    app.register_blueprint(user_app)
    app.register_blueprint(shelf_app)
    app.register_blueprint(goal_app)

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
