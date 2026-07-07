from __future__ import annotations

import os
from pathlib import Path

from flask import Flask, session, url_for
from werkzeug.middleware.proxy_fix import ProxyFix

from config import get_config
from . import storage
from .routes import bp
from .storage import close_db, init_db


def _is_truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _resolve_instance_path(raw_path: str | Path | None) -> Path:
    if raw_path is None:
        return _project_root() / "instance"

    instance_path = Path(raw_path).expanduser()
    if not instance_path.is_absolute():
        instance_path = (_project_root() / instance_path).resolve()
    return instance_path


def create_app(test_config: dict | None = None) -> Flask:
    config_object = get_config()
    instance_path = _resolve_instance_path(getattr(config_object, "INSTANCE_PATH", None))

    app = Flask(__name__, instance_path=str(instance_path), instance_relative_config=True)
    app.config.from_object(config_object)
    app.config.from_mapping(
        INSTANCE_PATH=str(instance_path),
        DATABASE=str(instance_path / "scootprime.db"),
        BACKUP_DIR=str(instance_path / "backups"),
        BRAND_DIR=str(instance_path / "brand"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    if os.environ.get("FLASK_ENV", "development").strip().lower() == "production":
        app.config["PREFERRED_URL_SCHEME"] = "https"
        app.config["SESSION_COOKIE_SECURE"] = _is_truthy(os.environ.get("SESSION_COOKIE_SECURE", "1"))
    else:
        app.config.setdefault("SESSION_COOKIE_SECURE", False)

    if test_config:
        app.config.update(test_config)

    if _is_truthy(os.environ.get("TRUST_PROXY", "0")):
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)

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
                "repair_active_count": storage.count_repair_orders_by_state().get("em_reparacao", 0),
                "current_user": current_user,
                "brand_logo_url": brand_logo_url,
            }
        except Exception:
            return {"stock_low_count": 0, "current_user": current_user, "brand_logo_url": brand_logo_url}

    app.register_blueprint(bp)
    return app
