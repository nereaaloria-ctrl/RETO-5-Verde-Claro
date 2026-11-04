# Configuración de la aplicación Flask
import os
from flask import Flask
from .db import close_db, initialize_db
from .routes import bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(DATABASE=os.environ.get("DATABASE_PATH", os.path.abspath("instance/prestamos.sqlite3")))
    if test_config:
        app.config.update(test_config)
    app.register_blueprint(bp)
    app.teardown_appcontext(close_db)
    with app.app_context():
        initialize_db()
    return app
