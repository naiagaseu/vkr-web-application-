from flask import Flask, redirect, url_for
from .extensions import db, migrate
from .config import Config

from .models import core_models
from .models import scoring_models
from .models import session_models

from .routes.test_routes import test_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)

    @app.route('/')
    def index_redirect():
        return redirect(url_for('test.index'))

    app.register_blueprint(test_bp)

    return app
