from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, session, url_for

from . import storage
from .routes import bp
from .storage import close_db, init_db


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SCOOTPRIME_SECRET", "dev-scootprime-local"),
        DATABASE=str(Path(app.instance_path) / "scootprime.db"),
        BACKUP_DIR=str(Path(app.instance_path) / "backups"),
        BRAND_DIR=str(Path(app.instance_path) / "brand"),
    )

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)
    Path(app.config["BACKUP_DIR"]).mkdir(parents=True, exist_ok=True)
    Path(app.config["BRAND_DIR"]).mkdir(parents=True, exist_ok=True)
    app.teardown_appcontext(close_db)

    with app.app_context():
        init_db()

    @app.context_processor
    def inject_app_status():
        current_user = storage.get_user(session.get("user_id")) if session.get("user_id") else None
        brand_logo_url = None
        try:
            if storage.get_brand_logo():
                brand_logo_url = url_for("web.brand_image")
            return {
                "stock_low_count": storage.count_low_stock(),
                "current_user": current_user,
                "brand_logo_url": brand_logo_url,
            }
        except Exception:
            return {"stock_low_count": 0, "current_user": current_user, "brand_logo_url": brand_logo_url}

    app.register_blueprint(bp)
    return app
