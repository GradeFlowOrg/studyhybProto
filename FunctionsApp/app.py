from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, jsonify

from FunctionsApp.api import api_bp
from DataBase.db_ext import db, login_manager, migrate
from DataBase.models import User


BASE_DIR = Path(__file__).resolve().parent

def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.getenv('SECRET_KEY', 'dev-key'),
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{BASE_DIR / 'studyhub.db'}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    login_manager.login_view = "api.login"

    @login_manager.user_loader
    def load_user(user_id: int) -> User | None:
        return db.session.get(User, int(user_id))

    @app.get('/')
    def healthcheck():
        return jsonify({'ok': True, 'service': 'studyhub-api'})

    app.register_blueprint(api_bp,prefix='/api_bp')
    return app

app = create_app()

if __name__ == '__main__':
    app.run()
